"""Knowledge base management routes."""

from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.auth import get_current_user
from api.dependencies.database import get_db
from core.exceptions import NotFoundError
from models.user import User
from schemas.knowledge import (
    DocumentResponse,
    IngestURLRequest,
    CollectionResponse,
    CollectionCreate,
)
from schemas.common import PaginatedResponse
from services.rag.ingestion import ingestion_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=PaginatedResponse)
async def list_documents(
    collection_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """List knowledge base documents."""
    try:
        from repositories.knowledge import KnowledgeDocumentRepository

        repo = KnowledgeDocumentRepository()
        filters: dict = {"tenant_id": current_user.tenant_id}
        if collection_id:
            filters["collection_id"] = collection_id
        if status_filter:
            filters["status"] = status_filter

        documents, total = await repo.list_filtered(
            db,
            filters=filters,
            offset=(page - 1) * page_size,
            limit=page_size,
        )

        return DocumentResponse(
            items=[DocumentResponse.model_validate(d) for d in documents],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size if total > 0 else 0,
        )
    except Exception as e:
        logger.error("list_documents_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    collection_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Upload a document to the knowledge base."""
    try:
        import aiofiles
        import os

        # Save file to disk
        upload_dir = f"/tmp/kb_uploads/{current_user.tenant_id}"
        os.makedirs(upload_dir, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "txt"
        file_path = os.path.join(upload_dir, f"{file_id}.{file_ext}")

        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Ingest the document
        document = await ingestion_service.ingest_document(
            db=db,
            tenant_id=current_user.tenant_id,
            file_path_or_url=file_path,
            title=title or file.filename or "Untitled",
            source_type="file",
            collection_id=collection_id,
            metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(content),
            },
        )

        logger.info(
            "document_uploaded",
            tenant_id=current_user.tenant_id,
            filename=file.filename,
        )
        return DocumentResponse.model_validate(document)
    except Exception as e:
        logger.error("upload_document_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Get a document by ID."""
    try:
        from repositories.knowledge import KnowledgeDocumentRepository

        repo = KnowledgeDocumentRepository()
        document = await repo.get_by_id(db, document_id)

        if not document:
            raise NotFoundError(f"Document {document_id} not found")

        if getattr(document, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"Document {document_id} not found")

        return DocumentResponse.model_validate(document)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("get_document_failed", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a document and its chunks from the knowledge base."""
    try:
        from repositories.knowledge import KnowledgeDocumentRepository, KnowledgeChunkRepository

        doc_repo = KnowledgeDocumentRepository()
        chunk_repo = KnowledgeChunkRepository()

        document = await doc_repo.get_by_id(db, document_id)
        if not document:
            raise NotFoundError(f"Document {document_id} not found")

        if getattr(document, "tenant_id", None) != current_user.tenant_id:
            raise NotFoundError(f"Document {document_id} not found")

        # Delete chunks first
        await chunk_repo.delete_by_document(db, document_id)
        # Delete document
        await doc_repo.delete(db, document_id)

        logger.info("document_deleted", document_id=document_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("delete_document_failed", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


@router.post("/ingest-url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_url(
    request: IngestURLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Ingest a document from a URL."""
    try:
        document = await ingestion_service.ingest_document(
            db=db,
            tenant_id=current_user.tenant_id,
            file_path_or_url=str(request.url),
            title=request.title or str(request.url),
            source_type="url",
            collection_id=request.collection_id,
        )

        logger.info(
            "url_ingested",
            tenant_id=current_user.tenant_id,
            url=str(request.url),
        )
        return DocumentResponse.model_validate(document)
    except Exception as e:
        logger.error("ingest_url_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest URL",
        )


@router.get("/collections", response_model=list[CollectionResponse])
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CollectionResponse]:
    """List knowledge base collections."""
    try:
        from repositories.knowledge import KnowledgeCollectionRepository

        repo = KnowledgeCollectionRepository()
        collections = await repo.list_by_tenant(db, current_user.tenant_id)
        return [CollectionResponse.model_validate(c) for c in collections]
    except Exception as e:
        logger.error("list_collections_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list collections",
        )


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollectionResponse:
    """Create a new knowledge base collection."""
    try:
        from repositories.knowledge import KnowledgeCollectionRepository

        repo = KnowledgeCollectionRepository()
        collection = await repo.create(
            db,
            {
                "id": str(uuid.uuid4()),
                "tenant_id": current_user.tenant_id,
                "name": request.name,
                "description": request.description or "",
            },
        )

        logger.info(
            "collection_created",
            tenant_id=current_user.tenant_id,
            name=request.name,
        )
        return CollectionResponse.model_validate(collection)
    except Exception as e:
        logger.error("create_collection_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection",
        )
