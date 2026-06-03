from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class Document(IDMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uploaded",
        index=True,
    )
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    entity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relationship_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_duplicate_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extracted_character_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_chunk_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_chunk_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    uploaded_by = relationship("User")
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    entities = relationship(
        "RagEntity",
        back_populates="document",
        cascade="all, delete-orphan",
        foreign_keys="RagEntity.document_id",
    )
    relationships = relationship(
        "RagRelationship",
        back_populates="document",
        cascade="all, delete-orphan",
        foreign_keys="RagRelationship.document_id",
    )

    @property
    def conflict_warning(self) -> str | None:
        # Conflict is detected from retrieved graph relationships, not document text.
        return None

    @property
    def uploaded_by_name(self) -> str | None:
        return self.uploaded_by.full_name if self.uploaded_by else None


class DocumentChunk(IDMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    document = relationship("Document", back_populates="chunks")
    entities = relationship(
        "RagEntity",
        back_populates="chunk",
        cascade="all, delete-orphan",
        foreign_keys="RagEntity.chunk_id",
    )
    relationships = relationship(
        "RagRelationship",
        back_populates="chunk",
        cascade="all, delete-orphan",
        foreign_keys="RagRelationship.chunk_id",
    )

    @property
    def document_title(self) -> str:
        return self.document.title


class RagEntity(IDMixin, TimestampMixin, Base):
    __tablename__ = "rag_entities"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    document = relationship(
        "Document",
        back_populates="entities",
        foreign_keys=[document_id],
    )
    chunk = relationship(
        "DocumentChunk",
        back_populates="entities",
        foreign_keys=[chunk_id],
    )
    source_relationships = relationship(
        "RagRelationship",
        back_populates="source_entity",
        cascade="all, delete-orphan",
        foreign_keys="RagRelationship.source_entity_id",
    )
    target_relationships = relationship(
        "RagRelationship",
        back_populates="target_entity",
        cascade="all, delete-orphan",
        foreign_keys="RagRelationship.target_entity_id",
    )


class RagRelationship(IDMixin, TimestampMixin, Base):
    __tablename__ = "rag_relationships"

    source_entity_id: Mapped[int] = mapped_column(
        ForeignKey("rag_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_entity_id: Mapped[int] = mapped_column(
        ForeignKey("rag_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    source_entity = relationship(
        "RagEntity",
        back_populates="source_relationships",
        foreign_keys=[source_entity_id],
    )
    target_entity = relationship(
        "RagEntity",
        back_populates="target_relationships",
        foreign_keys=[target_entity_id],
    )
    document = relationship(
        "Document",
        back_populates="relationships",
        foreign_keys=[document_id],
    )
    chunk = relationship(
        "DocumentChunk",
        back_populates="relationships",
        foreign_keys=[chunk_id],
    )


class RagChatLog(IDMixin, TimestampMixin, Base):
    __tablename__ = "rag_chat_logs"

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    retrieved_context_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    user = relationship("User")
