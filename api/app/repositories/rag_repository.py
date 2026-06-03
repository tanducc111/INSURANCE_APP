from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.rag import (
    Document,
    DocumentChunk,
    RagChatLog,
    RagEntity,
    RagRelationship,
)


def _document_options():
    return (joinedload(Document.uploaded_by),)


def _chunk_options():
    return (joinedload(DocumentChunk.document),)


def _entity_options():
    return (
        joinedload(RagEntity.document),
        joinedload(RagEntity.chunk),
    )


def _relationship_options():
    return (
        joinedload(RagRelationship.document),
        joinedload(RagRelationship.chunk),
        joinedload(RagRelationship.source_entity),
        joinedload(RagRelationship.target_entity),
    )


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
        source_file_path: str | None = None,
        processing_status: str = "uploaded",
    ) -> Document:
        document = Document(
            title=title,
            file_name=file_name,
            content_type=content_type,
            raw_text=raw_text,
            source_file_path=source_file_path,
            processing_status=processing_status,
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
            .where(Document.processing_status == "completed")
            .order_by(DocumentChunk.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(query))

    @staticmethod
    def delete_for_document(db: Session, document_id: int) -> None:
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()


class RagEntityRepository:
    @staticmethod
    def create_entity(
        db: Session,
        *,
        document_id: int,
        chunk_id: int | None,
        name: str,
        entity_type: str,
        description: str,
    ) -> RagEntity:
        entity = RagEntity(
            document_id=document_id,
            chunk_id=chunk_id,
            name=name,
            entity_type=entity_type,
            description=description,
        )
        db.add(entity)
        return entity

    @staticmethod
    def list_for_document(db: Session, document_id: int) -> list[RagEntity]:
        return list(
            db.scalars(
                select(RagEntity)
                .options(*_entity_options())
                .where(RagEntity.document_id == document_id)
                .order_by(RagEntity.name.asc())
            )
        )

    @staticmethod
    def search_entities(
        db: Session,
        *,
        keywords: list[str],
        limit: int = 20,
    ) -> list[RagEntity]:
        if not keywords:
            return []
        filters = [
            func.lower(RagEntity.name).like(f"%{keyword.lower()}%")
            | func.lower(RagEntity.description).like(f"%{keyword.lower()}%")
            for keyword in keywords
            if len(keyword) >= 2
        ]
        if not filters:
            return []
        query = (
            select(RagEntity)
            .options(*_entity_options())
            .join(RagEntity.document)
            .where(or_(*filters))
            .where(Document.processing_status == "completed")
            .order_by(RagEntity.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(query).unique())

    @staticmethod
    def list_by_chunk_ids(db: Session, chunk_ids: list[int]) -> list[RagEntity]:
        if not chunk_ids:
            return []
        return list(
            db.scalars(
                select(RagEntity)
                .options(*_entity_options())
                .join(RagEntity.document)
                .where(RagEntity.chunk_id.in_(chunk_ids))
                .where(Document.processing_status == "completed")
                .order_by(RagEntity.name.asc())
            )
        )

    @staticmethod
    def delete_for_document(db: Session, document_id: int) -> None:
        db.query(RagEntity).filter(RagEntity.document_id == document_id).delete()


class RagRelationshipRepository:
    @staticmethod
    def create_relationship(
        db: Session,
        *,
        source_entity_id: int,
        target_entity_id: int,
        relationship_type: str,
        description: str,
        document_id: int,
        chunk_id: int | None,
    ) -> RagRelationship:
        relationship = RagRelationship(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            relationship_type=relationship_type,
            description=description,
            document_id=document_id,
            chunk_id=chunk_id,
        )
        db.add(relationship)
        return relationship

    @staticmethod
    def list_for_document(db: Session, document_id: int) -> list[RagRelationship]:
        return list(
            db.scalars(
                select(RagRelationship)
                .options(*_relationship_options())
                .where(RagRelationship.document_id == document_id)
                .order_by(RagRelationship.created_at.desc())
            )
        )

    @staticmethod
    def list_connected(
        db: Session,
        *,
        entity_ids: list[int],
        limit: int = 50,
    ) -> list[RagRelationship]:
        if not entity_ids:
            return []
        query = (
            select(RagRelationship)
            .options(*_relationship_options())
            .join(RagRelationship.document)
            .where(
                (RagRelationship.source_entity_id.in_(entity_ids))
                | (RagRelationship.target_entity_id.in_(entity_ids))
            )
            .where(Document.processing_status == "completed")
            .order_by(RagRelationship.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(query).unique())

    @staticmethod
    def delete_for_document(db: Session, document_id: int) -> None:
        db.query(RagRelationship).filter(
            RagRelationship.document_id == document_id
        ).delete()


class RagChatLogRepository:
    @staticmethod
    def create_log(
        db: Session,
        *,
        user_id: int | None,
        question: str,
        answer: str,
        retrieved_context_json: dict,
        confidence_score: float,
    ) -> RagChatLog:
        log = RagChatLog(
            user_id=user_id,
            question=question,
            answer=answer,
            retrieved_context_json=retrieved_context_json,
            confidence_score=confidence_score,
        )
        db.add(log)
        return log
