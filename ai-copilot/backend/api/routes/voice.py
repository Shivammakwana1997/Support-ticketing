"""Voice API routes - transcription, synthesis, and call management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError
from models.user import User
from schemas.voice import (
    TranscribeResponse,
    SynthesizeRequest,
    SynthesizeResponse,
    VoiceCallResponse,
    VoiceCallCreate,
    CallSummaryResponse,
)
from services.voice.transcription import transcription_service
from services.voice.synthesis import synthesis_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(None),
    current_user: User = Depends(get_current_user),
) -> TranscribeResponse:
    """Transcribe an audio file to text."""
    try:
        audio_data = await file.read()
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file",
            )

        # Determine format from filename
        audio_format = "wav"
        if file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in ("mp3", "wav", "m4a", "ogg", "webm", "flac"):
                audio_format = ext

        result = await transcription_service.transcribe(
            audio_data=audio_data,
            format=audio_format,
            language=language,
        )

        logger.info(
            "audio_transcribed",
            user_id=str(current_user.id),
            format=audio_format,
            text_length=len(result.get("text", "")),
        )
        return TranscribeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("transcription_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription failed",
        )


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
) -> SynthesizeResponse:
    """Synthesize text to speech."""
    try:
        result = await synthesis_service.synthesize(
            text=request.text,
            voice=request.voice or "alloy",
            response_format=request.response_format or "mp3",
        )

        logger.info(
            "speech_synthesized",
            user_id=str(current_user.id),
            text_length=len(request.text),
            voice=request.voice,
        )

        # If audio_data is bytes, we need to return a URL instead
        if isinstance(result.get("audio_data"), bytes):
            try:
                url = await synthesis_service.synthesize_to_url(
                    text=request.text,
                    voice=request.voice or "alloy",
                )
                return SynthesizeResponse(
                    audio_url=url,
                    format=request.response_format or "mp3",
                    duration_estimate_seconds=result.get("duration_estimate_seconds", 0.0),
                )
            except Exception:
                # Fallback: return metadata without URL
                return SynthesizeResponse(
                    audio_url="",
                    format=request.response_format or "mp3",
                    duration_estimate_seconds=result.get("duration_estimate_seconds", 0.0),
                )

        return SynthesizeResponse(**result)

    except Exception as e:
        logger.error("synthesis_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Speech synthesis failed",
        )


@router.get("/calls/{call_id}", response_model=VoiceCallResponse)
async def get_call(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceCallResponse:
    """Get voice call details."""
    try:
        from repositories.voice_call import VoiceCallRepository

        repo = VoiceCallRepository()
        call = await repo.get_by_id(db, call_id)
        if not call:
            raise NotFoundError(f"Call {call_id} not found")

        if getattr(call, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"Call {call_id} not found")

        return VoiceCallResponse.model_validate(call)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_call_failed", call_id=call_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get call",
        )


@router.post("/calls", response_model=VoiceCallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    request: VoiceCallCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoiceCallResponse:
    """Initiate a new voice call."""
    try:
        from repositories.voice_call import VoiceCallRepository

        repo = VoiceCallRepository()
        call = await repo.create(
            db,
            {
                "id": str(uuid.uuid4()),
                "tenant_id": current_user.tenant_id,
                "customer_id": request.customer_id,
                "agent_id": request.agent_id or str(current_user.id),
                "conversation_id": request.conversation_id,
                "direction": request.direction or "outbound",
                "status": "initiated",
                "started_at": datetime.now(timezone.utc),
            },
        )

        logger.info(
            "call_created",
            call_id=call.id if hasattr(call, "id") else str(call),
            tenant_id=current_user.tenant_id,
        )
        return VoiceCallResponse.model_validate(call)
    except Exception as e:
        logger.error("create_call_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create call",
        )


@router.post("/calls/{call_id}/summary", response_model=CallSummaryResponse)
async def get_call_summary(
    call_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CallSummaryResponse:
    """Get an AI-generated summary of a voice call."""
    try:
        from repositories.voice_call import VoiceCallRepository
        from integrations.openai_client import openai_client

        repo = VoiceCallRepository()
        call = await repo.get_by_id(db, call_id)
        if not call:
            raise NotFoundError(f"Call {call_id} not found")

        if getattr(call, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"Call {call_id} not found")

        # Get transcript if available
        transcript = getattr(call, "transcript", "") or ""

        if not transcript:
            return CallSummaryResponse(
                call_id=call_id,
                summary="No transcript available for this call.",
                key_topics=[],
                action_items=[],
                sentiment="neutral",
            )

        response = await openai_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Summarize this customer support call transcript. "
                        "Provide: 1) A brief summary, 2) Key topics discussed, "
                        "3) Action items, 4) Overall customer sentiment."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            model="gpt-4o",
            temperature=0.3,
        )

        summary_text = response.choices[0].message.content or ""

        return CallSummaryResponse(
            call_id=call_id,
            summary=summary_text,
            key_topics=[],
            action_items=[],
            sentiment="neutral",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_call_summary_failed", call_id=call_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate call summary",
        )
