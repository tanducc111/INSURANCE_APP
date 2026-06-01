from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    file_name: str
    content_type: str
    chunk_count: int
    entity_count: int
    relationship_count: int
    uploaded_by_user_id: int | None
    uploaded_by_name: str | None
    created_at: datetime
    updated_at: datetime


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    token_count: int
    created_at: datetime
    updated_at: datetime


class ChatbotQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ChatbotSource(BaseModel):
    document_id: int
    document_title: str
    chunk_id: int
    chunk_index: int
    score: float
    preview: str


class ChatbotMatchedEntity(BaseModel):
    id: int
    name: str
    entity_type: str
    description: str


class ChatbotAnswer(BaseModel):
    answer: str
    sources: list[ChatbotSource]
    confidence_score: float = 0.0
    matched_entities: list[ChatbotMatchedEntity] = Field(default_factory=list)
    fallback_reason: str | None = None
