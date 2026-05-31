import io
import math
import re
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rag import Document, DocumentChunk
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.rag_repository import DocumentChunkRepository, DocumentRepository
from app.schemas.rag import ChatbotAnswer, ChatbotQuestion, ChatbotSource


TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if len(token) > 1]


class EmbeddingService:
    def embed(self, text: str) -> dict[str, float]:
        raise NotImplementedError


class LocalEmbeddingService(EmbeddingService):
    def embed(self, text: str) -> dict[str, float]:
        counts: dict[str, float] = {}
        for token in _tokens(text):
            counts[token] = counts.get(token, 0.0) + 1.0
        length = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {token: value / length for token, value in counts.items()}


def get_embedding_service() -> EmbeddingService:
    if settings.EMBEDDING_PROVIDER != "local" and not settings.EMBEDDING_API_KEY:
        return LocalEmbeddingService()
    return LocalEmbeddingService()


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


def _cosine_score(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF extraction dependency is not installed",
        ) from exc

    reader = PdfReader(io.BytesIO(content))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page_texts)


def _extract_text(file_name: str, content_type: str, content: bytes) -> str:
    lower_name = file_name.lower()
    if content_type == "application/pdf" or lower_name.endswith(".pdf"):
        return _extract_pdf_text(content)
    if (
        content_type.startswith("text/")
        or lower_name.endswith(".txt")
        or lower_name.endswith(".md")
    ):
        return _decode_text(content)
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Only PDF, TXT, and Markdown documents are supported",
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        boundary = normalized.rfind(". ", start, end)
        if boundary > start + chunk_size // 2:
            end = boundary + 1
        chunks.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


class DocumentService:
    @staticmethod
    async def upload_document(
        db: Session,
        *,
        file: UploadFile,
        title: str | None,
        actor: User,
    ) -> Document:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uploaded document is empty",
            )

        content_type = file.content_type or "application/octet-stream"
        raw_text = _extract_text(file.filename or "document", content_type, content)
        raw_text = _normalize_text(raw_text)
        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text was found in the document",
            )

        chunks = _chunk_text(raw_text)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Document could not be chunked",
            )

        document = DocumentRepository.create_document(
            db,
            title=title or file.filename or "Company document",
            file_name=file.filename or "document",
            content_type=content_type,
            raw_text=raw_text,
            uploaded_by_user_id=actor.id,
        )
        db.flush()

        embedding_service = get_embedding_service()
        for index, chunk_text in enumerate(chunks):
            embedding = embedding_service.embed(chunk_text)
            DocumentChunkRepository.create_chunk(
                db,
                document_id=document.id,
                chunk_index=index,
                content=chunk_text,
                embedding_json=embedding,
                token_count=len(_tokens(chunk_text)),
            )

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.document.upload",
            entity_type="document",
            entity_id=str(document.id),
            metadata_json={"file_name": document.file_name, "chunks": len(chunks)},
        )
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def list_documents(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Document]:
        return DocumentRepository.list_documents(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
        )

    @staticmethod
    def list_chunks(
        db: Session,
        *,
        document_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentChunk]:
        document = DocumentRepository.get_by_id(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return DocumentChunkRepository.list_for_document(
            db,
            document_id,
            skip=skip,
            limit=min(limit, 200),
        )

    @staticmethod
    def delete_document(db: Session, *, document_id: int, actor: User) -> None:
        document = DocumentRepository.get_by_id(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.document.delete",
            entity_type="document",
            entity_id=str(document.id),
            metadata_json={"file_name": document.file_name},
        )
        DocumentRepository.delete_document(db, document)
        db.commit()


class RetrievalService:
    @staticmethod
    def retrieve(db: Session, question: str) -> list[RetrievedChunk]:
        question_embedding = get_embedding_service().embed(question)
        chunks = DocumentChunkRepository.list_all_chunks(db)
        scored = [
            RetrievedChunk(
                chunk=chunk,
                score=_cosine_score(question_embedding, chunk.embedding_json),
            )
            for chunk in chunks
        ]
        scored = [item for item in scored if item.score >= settings.RAG_MIN_SCORE]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: settings.RAG_TOP_K]


class ChatbotService:
    @staticmethod
    def answer_question(
        db: Session,
        *,
        payload: ChatbotQuestion,
        actor: User,
    ) -> ChatbotAnswer:
        retrieved = RetrievalService.retrieve(db, payload.question)
        if not retrieved:
            return ChatbotAnswer(
                answer=(
                    "Information is not available in the uploaded company "
                    "documents."
                ),
                sources=[],
            )

        sources = [
            ChatbotSource(
                document_id=item.chunk.document_id,
                document_title=item.chunk.document_title,
                chunk_id=item.chunk.id,
                chunk_index=item.chunk.chunk_index,
                score=round(item.score, 4),
                preview=item.chunk.content[:240],
            )
            for item in retrieved
        ]
        context_lines = [
            f"- {item.chunk.content[:700]}" for item in retrieved[: settings.RAG_TOP_K]
        ]
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.chatbot.query",
            entity_type="document_chunks",
            metadata_json={"source_chunk_ids": [item.chunk.id for item in retrieved]},
        )
        db.commit()
        return ChatbotAnswer(
            answer=(
                "Based on uploaded company documents, the relevant information is:\n"
                + "\n".join(context_lines)
            ),
            sources=sources,
        )
