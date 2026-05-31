from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.db.session import get_db
from app.models.rag import Document, DocumentChunk
from app.models.user import User, UserRole
from app.schemas.rag import (
    ChatbotAnswer,
    ChatbotQuestion,
    DocumentChunkRead,
    DocumentRead,
)
from app.services.rag_service import ChatbotService, DocumentService

router = APIRouter(tags=["rag"])


@router.post(
    "/admin/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Document:
    return await DocumentService.upload_document(
        db,
        file=file,
        title=title,
        actor=current_admin,
    )


@router.get("/admin/documents", response_model=list[DocumentRead])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[Document]:
    _ = current_admin
    return DocumentService.list_documents(
        db,
        skip=skip,
        limit=limit,
        search=search,
    )


@router.get(
    "/admin/documents/{document_id}/chunks",
    response_model=list[DocumentChunkRead],
)
async def list_document_chunks(
    document_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[DocumentChunk]:
    _ = current_admin
    return DocumentService.list_chunks(
        db,
        document_id=document_id,
        skip=skip,
        limit=limit,
    )


@router.delete("/admin/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
) -> Response:
    DocumentService.delete_document(db, document_id=document_id, actor=current_admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/customer/chatbot/query", response_model=ChatbotAnswer)
async def ask_chatbot(
    payload: ChatbotQuestion,
    db: Session = Depends(get_db),
    current_customer: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> ChatbotAnswer:
    return ChatbotService.answer_question(
        db,
        payload=payload,
        actor=current_customer,
    )
