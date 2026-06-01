from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rag import RagEntity, RagRelationship
from app.repositories.rag_repository import (
    DocumentChunkRepository,
    RagEntityRepository,
    RagRelationshipRepository,
)
from app.services.rag_service import (
    RetrievedChunk,
    _cosine_score,
    _tokens,
    get_embedding_service,
)


@dataclass
class GraphRetrievalResult:
    chunks: list[RetrievedChunk]
    matched_entities: list[RagEntity]
    relationships: list[RagRelationship]
    context_text: str
    graph_context: str
    confidence_score: float
    fallback_reason: str | None = None


def _keywords(question: str) -> list[str]:
    tokens = _tokens(question)
    important = [token for token in tokens if len(token) >= 3]
    phrases = [
        "bảo hiểm sức khỏe",
        "bảo hiểm xe máy",
        "bồi thường",
        "hồ sơ",
        "giấy tờ",
        "quyền lợi",
        "thời gian",
        "tai nạn",
        "thú cưng",
    ]
    lower_question = question.lower()
    important.extend(phrase for phrase in phrases if phrase in lower_question)
    return list(dict.fromkeys(important))[:20]


def _has_unsupported_specific_term(question: str, context_text: str, graph_context: str) -> bool:
    lower_question = question.lower()
    combined_context = f"{context_text}\n{graph_context}".lower()
    unsupported_terms = [
        "thú cưng",
        "chó",
        "mèo",
        "vật nuôi",
        "pet",
    ]
    return any(term in lower_question and term not in combined_context for term in unsupported_terms)


class GraphRagRetrievalService:
    @staticmethod
    def _context_for_chunk(item: RetrievedChunk, *, max_length: int = 1200) -> str:
        chunk_content = item.chunk.content.strip()
        raw_text = getattr(item.chunk.document, "raw_text", "") or ""
        if not raw_text or not chunk_content:
            return chunk_content[:max_length]

        anchor = chunk_content[: min(120, len(chunk_content))]
        start_index = raw_text.find(anchor)
        if start_index < 0:
            return chunk_content[:max_length]

        sentence_start = raw_text.rfind(". ", 0, start_index)
        if sentence_start >= 0:
            start_index = sentence_start + 2
        else:
            start_index = max(0, raw_text.rfind(" ", 0, start_index))

        end_index = min(len(raw_text), start_index + max_length)
        sentence_end = raw_text.find(". ", start_index + len(chunk_content), end_index + 200)
        if sentence_end > 0:
            end_index = min(len(raw_text), sentence_end + 1)
        return raw_text[start_index:end_index].strip()

    @staticmethod
    def retrieve(db: Session, question: str) -> GraphRetrievalResult:
        question_embedding = get_embedding_service().embed(question)
        all_chunks = DocumentChunkRepository.list_all_chunks(db)
        scored = [
            RetrievedChunk(
                chunk=chunk,
                score=_cosine_score(question_embedding, chunk.embedding_json),
            )
            for chunk in all_chunks
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        relevant_chunks = [
            item for item in scored if item.score >= settings.RAG_MIN_SCORE
        ][: settings.RAG_TOP_K]

        question_keywords = _keywords(question)
        matched_entities = RagEntityRepository.search_entities(
            db,
            keywords=question_keywords,
            limit=20,
        )
        chunk_entities = RagEntityRepository.list_by_chunk_ids(
            db,
            [item.chunk.id for item in relevant_chunks],
        )
        entity_by_id = {entity.id: entity for entity in matched_entities + chunk_entities}
        matched_entities = list(entity_by_id.values())[:30]

        relationships = RagRelationshipRepository.list_connected(
            db,
            entity_ids=[entity.id for entity in matched_entities],
            limit=60,
        )

        chunk_ids_from_graph = {
            relationship.chunk_id for relationship in relationships if relationship.chunk_id
        } | {entity.chunk_id for entity in matched_entities if entity.chunk_id}
        current_chunk_ids = {item.chunk.id for item in relevant_chunks}
        for chunk in all_chunks:
            if chunk.id in chunk_ids_from_graph and chunk.id not in current_chunk_ids:
                relevant_chunks.append(RetrievedChunk(chunk=chunk, score=settings.RAG_MIN_SCORE))
                current_chunk_ids.add(chunk.id)
            if len(relevant_chunks) >= settings.RAG_TOP_K + 3:
                break

        best_chunk_score = max((item.score for item in relevant_chunks), default=0.0)
        graph_score = min(0.4, 0.04 * len(matched_entities) + 0.02 * len(relationships))
        confidence_score = round(min(1.0, best_chunk_score + graph_score), 4)

        context_text = "\n\n".join(
            (
                f"Tài liệu: {item.chunk.document_title}\n"
                f"Đoạn {item.chunk.chunk_index + 1}:\n"
                f"{GraphRagRetrievalService._context_for_chunk(item)}"
            )
            for item in relevant_chunks
        )
        graph_context = "\n".join(
            [
                "Thực thể liên quan:",
                *[
                    f"- {entity.name} ({entity.entity_type}): {entity.description}"
                    for entity in matched_entities[:20]
                ],
                "Quan hệ:",
                *[
                    (
                        f"- {relationship.source_entity.name} "
                        f"{relationship.relationship_type} "
                        f"{relationship.target_entity.name}: {relationship.description}"
                    )
                    for relationship in relationships[:30]
                ],
            ]
        )

        fallback_reason = None
        if not relevant_chunks and not matched_entities:
            fallback_reason = "Không tìm thấy đoạn tài liệu hoặc thực thể phù hợp."
            confidence_score = 0.0
        elif _has_unsupported_specific_term(question, context_text, graph_context):
            fallback_reason = "Câu hỏi có chủ đề cụ thể không xuất hiện trong tài liệu nội bộ."
            confidence_score = 0.0
        elif confidence_score < settings.RAG_MIN_SCORE:
            fallback_reason = "Ngữ cảnh truy xuất chưa đủ mạnh."

        return GraphRetrievalResult(
            chunks=relevant_chunks,
            matched_entities=matched_entities,
            relationships=relationships,
            context_text=context_text,
            graph_context=graph_context,
            confidence_score=confidence_score,
            fallback_reason=fallback_reason,
        )
