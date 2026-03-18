"""Chat routes including WebSocket for real-time communication."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError
from models.user import User
from models.enums import SenderTypeEnum
from schemas.message import MessageResponse
from services.agents.chatbot import chatbot_service
from services.conversation import conversation_service

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["chat"])


@router.websocket("/api/v1/ws/chat/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
) -> None:
    """WebSocket endpoint for real-time chat.

    Protocol:
    - Client sends: {"type": "message", "content": "...", "sender_id": "..."}
    - Server sends: {"type": "typing", "sender": "ai"}
    - Server sends: {"type": "chunk", "content": "partial text"}
    - Server sends: {"type": "message", "content": "full response", "citations": [...]}
    - Server sends: {"type": "error", "content": "error message"}
    """
    await websocket.accept()

    # Authenticate via query param or first message
    try:
        token = websocket.query_params.get("token", "")
        db = None

        async for db_session in get_db_ws():
            db = db_session
            break

        if not db:
            await websocket.send_json({"type": "error", "content": "Database unavailable"})
            await websocket.close()
            return

        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.send_json({"type": "error", "content": "Authentication required"})
            await websocket.close(code=4001)
            return

        tenant_id = user.tenant_id
        logger.info(
            "websocket_connected",
            conversation_id=conversation_id,
            user_id=str(user.id),
        )

        # Verify conversation exists
        try:
            await conversation_service.get_conversation(
                db=db,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
        except NotFoundError:
            await websocket.send_json({"type": "error", "content": "Conversation not found"})
            await websocket.close(code=4004)
            return

        # Main message loop
        while True:
            try:
                raw_data = await websocket.receive_text()
                data = json.loads(raw_data)

                msg_type = data.get("type", "message")
                content = data.get("content", "").strip()

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                if msg_type != "message" or not content:
                    continue

                # Save user message
                await conversation_service.add_message(
                    db=db,
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    sender_type=SenderTypeEnum.CUSTOMER,
                    sender_id=data.get("sender_id", str(user.id)),
                    content=content,
                )

                # Send typing indicator
                await websocket.send_json({"type": "typing", "sender": "ai"})

                # Get AI response
                try:
                    result = await chatbot_service.get_response(
                        db=db,
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        user_message=content,
                    )

                    ai_response = result.get("response", "")
                    citations = result.get("citations", [])

                    # Save AI message
                    await conversation_service.add_message(
                        db=db,
                        tenant_id=tenant_id,
                        conversation_id=conversation_id,
                        sender_type=SenderTypeEnum.AI,
                        sender_id="system",
                        content=ai_response,
                    )

                    # Send complete response
                    await websocket.send_json({
                        "type": "message",
                        "content": ai_response,
                        "citations": citations,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "sender": "ai",
                    })

                except Exception as e:
                    logger.error(
                        "chat_ai_response_failed",
                        conversation_id=conversation_id,
                        error=str(e),
                    )
                    await websocket.send_json({
                        "type": "error",
                        "content": "Failed to generate response. Please try again.",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "content": "Invalid JSON format",
                })

    except WebSocketDisconnect:
        logger.info(
            "websocket_disconnected",
            conversation_id=conversation_id,
        )
    except Exception as e:
        logger.error(
            "websocket_error",
            conversation_id=conversation_id,
            error=str(e),
        )
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.post("/api/v1/chat/completions")
async def chat_completion(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Synchronous chat completion fallback.

    Request body:
        {
            "conversation_id": "...",
            "message": "...",
            "history": [{"role": "user", "content": "..."}, ...]
        }
    """
    conversation_id = request.get("conversation_id", "")
    message = request.get("message", "").strip()
    history = request.get("history")

    if not conversation_id or not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="conversation_id and message are required",
        )

    try:
        # Save user message
        await conversation_service.add_message(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
            sender_type=SenderTypeEnum.CUSTOMER,
            sender_id=str(current_user.id),
            content=message,
        )

        # Get AI response
        result = await chatbot_service.get_response(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
            user_message=message,
            history=history,
        )

        ai_response = result.get("response", "")

        # Save AI message
        await conversation_service.add_message(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
            sender_type=SenderTypeEnum.AI,
            sender_id="system",
            content=ai_response,
        )

        return {
            "response": ai_response,
            "citations": result.get("citations", []),
            "intent": result.get("intent"),
            "sentiment": result.get("sentiment"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("chat_completion_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat completion failed",
        )


@router.get("/api/v1/chat/conversations/{conversation_id}/history")
async def get_chat_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get chat conversation history."""
    try:
        result = await conversation_service.get_conversation(
            db=db,
            tenant_id=current_user.tenant_id,
            conversation_id=conversation_id,
        )
        messages = result.get("messages", [])
        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "id": getattr(m, "id", ""),
                    "sender_type": getattr(m, "sender_type", ""),
                    "sender_id": getattr(m, "sender_id", ""),
                    "content": getattr(m, "content", ""),
                    "created_at": getattr(m, "created_at", ""),
                }
                for m in messages
            ],
            "total": len(messages),
        }
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_chat_history_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chat history",
        )
