from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.rag import Document, DocumentChunk
def _document_options():
    return (
        joinedload(Document.uploaded_by),
        joinedload(Document.chunks),
    )


def _chunk_options():
    return (joinedload(DocumentChunk.document),)


class DocumentRepository:
    @staticmethod
    def get_by_id(db: Session, document_id: int) -> Document | None:
        return (
            db.scalars(
                select(Document)
                .options(*_document_options())
                .where(Document.id == document_id)
            )
            .unique()
            .first()
        )

    @staticmethod
    def list_documents(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Document]:
        query: Select[tuple[Document]] = (
            select(Document)
            .options(*_document_options())
            .order_by(Document.created_at.desc())
        )
        if search:
            pattern = f"%{search.lower()}%"
            query = query.where(
                func.lower(Document.title).like(pattern)
                | func.lower(Document.file_name).like(pattern)
            )
        return list(db.scalars(query.offset(skip).limit(limit)).unique())

    @staticmethod
    def create_document(
        db: Session,
        *,
        title: str,
        file_name: str,
        content_type: str,
        raw_text: str,
        uploaded_by_user_id: int | None,
    ) -> Document:
        document = Document(
            title=title,
            file_name=file_name,
            content_type=content_type,
            raw_text=raw_text,
            uploaded_by_user_id=uploaded_by_user_id,
        )
        db.add(document)
        return document

    @staticmethod
    def delete_document(db: Session, document: Document) -> None:
        db.delete(document)


class DocumentChunkRepository:
    @staticmethod
    def create_chunk(
        db: Session,
        *,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding_json: dict[str, float],
        token_count: int,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            embedding_json=embedding_json,
            token_count=token_count,
        )
        db.add(chunk)
        return chunk

    @staticmethod
    def list_for_document(
        db: Session,
        document_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentChunk]:
        query = (
            select(DocumentChunk)
            .options(*_chunk_options())
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(db.scalars(query.offset(skip).limit(limit)))

    @staticmethod
    def list_all_chunks(db: Session, *, limit: int = 1000) -> list[DocumentChunk]:
        query = (
            select(DocumentChunk)
            .options(*_chunk_options())
            .join(DocumentChunk.document)
            .order_by(DocumentChunk.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(query))
