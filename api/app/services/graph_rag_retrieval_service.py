import logging
import re
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


CONFLICT_REFUSAL_REASON = "conflicting_context"
UNSUPPORTED_QUERY_REASON = "unsupported_query"
LOW_CONFIDENCE_REASON = "low_confidence"
MIN_GRAPH_RAG_CONFIDENCE = 0.55
TOP_K_CHUNKS = 3
TOP_K_RELATIONSHIPS = 10
CONFLICT_RELATIONSHIP_TYPES = {"has_limit", "has_waiting_period", "payment_rule"}
logger = logging.getLogger(__name__)
QUERY_STOPWORDS = {
    "toi",
    "tôi",
    "ban",
    "bạn",
    "la",
    "là",
    "ai",
    "co",
    "có",
    "khong",
    "không",
    "bao",
    "bảo",
    "hiem",
    "hiểm",
    "duoc",
    "được",
    "khi",
    "neu",
    "nếu",
    "can",
    "cần",
    "gi",
    "gì",
    "cho",
    "ve",
    "về",
    "cua",
    "của",
}


@dataclass
class GraphRetrievalResult:
    chunks: list[RetrievedChunk]
    matched_entities: list[RagEntity]
    relationships: list[RagRelationship]
    context_text: str
    graph_context: str
    confidence_score: float
    fallback_reason: str | None = None
    classification: str = "unsupported"
    entity_match_score: float = 0.0
    relationship_match_score: float = 0.0
    chunk_similarity_score: float = 0.0


@dataclass
class RelationshipFact:
    source: str
    relationship_type: str
    target: str
    description: str = ""


def classify_query(question: str) -> str:
    normalized = _normalize_fact_text(question)
    unsupported_patterns = (
        "tôi là ai",
        "toi la ai",
        "bạn là ai",
        "ban la ai",
        "hôm nay",
        "hom nay",
        "thứ mấy",
        "thu may",
        "bitcoin",
        "thời tiết",
        "thoi tiet",
        "tin tức",
        "tin tuc",
        "chứng khoán",
        "chung khoan",
    )
    if any(pattern in normalized for pattern in unsupported_patterns):
        return "unsupported"

    appointment_terms = (
        "lịch hẹn",
        "lich hen",
        "đặt lịch",
        "dat lich",
        "hẹn nhân viên",
        "hen nhan vien",
    )
    if any(term in normalized for term in appointment_terms):
        return "appointment_support"

    claim_terms = (
        "bồi thường",
        "boi thuong",
        "hồ sơ",
        "ho so",
        "chứng từ",
        "chung tu",
        "giấy tờ",
        "giay to",
        "cần bổ sung",
        "can bo sung",
        "tai nạn",
        "tai nan",
        "hóa đơn",
        "hoa don",
        "đua xe",
        "dua xe",
    )
    if any(term in normalized for term in claim_terms):
        return "claim_process" if "bảo hiểm" not in normalized and "bao hiem" not in normalized else "insurance_knowledge"

    contract_terms = (
        "hợp đồng",
        "hop dong",
        "số hợp đồng",
        "so hop dong",
        "hiệu lực",
        "hieu luc",
        "phí bảo hiểm",
        "phi bao hiem",
        "thanh toán",
        "thanh toan",
        "hạn mức",
        "han muc",
    )
    if any(term in normalized for term in contract_terms):
        return "contract_information"

    insurance_terms = (
        "bảo hiểm",
        "bao hiem",
        "quyền lợi",
        "quyen loi",
        "gói",
        "goi",
        "chi trả",
        "chi tra",
        "hỗ trợ",
        "ho tro",
        "phẫu thuật",
        "phau thuat",
        "nội trú",
        "noi tru",
        "xe máy",
        "xe may",
        "ô tô",
        "o to",
        "sức khỏe",
        "suc khoe",
    )
    if any(term in normalized for term in insurance_terms):
        return "insurance_knowledge"

    return "unsupported"


def _allowed_relationship_types(classification: str, question: str) -> set[str]:
    normalized = _normalize_fact_text(question)
    if classification == "claim_process":
        return {"requires", "needs_document", "next_action", "handled_by", "related_to", "excludes"}
    if classification == "contract_information":
        return {"has_limit", "has_waiting_period", "payment_rule", "applies_to", "related_to"}
    if classification == "appointment_support":
        return {"handled_by", "related_to"}
    if classification == "insurance_knowledge":
        allowed = {"covers", "excludes", "applies_to"}
        if _conflict_relationship_types_for_question(question):
            allowed.add("has_limit")
        document_terms = ("giấy tờ", "giay to", "chứng từ", "chung tu", "hồ sơ", "ho so", "hóa đơn", "hoa don")
        if any(term in normalized for term in document_terms):
            allowed |= {"requires", "needs_document"}
        return allowed
    return set()


def _keywords(question: str) -> list[str]:
    lower_question = question.casefold()
    tokens = [
        token for token in _tokens(question)
        if len(token) >= 3 and token.casefold() not in QUERY_STOPWORDS
    ]
    phrases = [
        "bảo hiểm xe máy",
        "bảo hiểm ô tô",
        "bảo hiểm sức khỏe cao cấp",
        "bảo hiểm sức khỏe",
        "tai nạn xe máy",
        "hóa đơn sửa chữa",
        "biên lai sửa chữa",
        "hình ảnh hiện trường",
        "cần bổ sung hồ sơ",
        "bổ sung chứng từ",
        "thanh toán bồi thường",
        "đua xe",
        "phẫu thuật",
        "hồ sơ bồi thường",
        "giấy tờ",
        "chứng từ",
        "thú cưng",
        "vật nuôi",
        "chó",
        "mèo",
    ]
    tokens.extend(phrase for phrase in phrases if phrase.casefold() in lower_question)
    return list(dict.fromkeys(tokens))[:30]


def _chunk_matches_question(chunk_text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lower_text = chunk_text.casefold()
    strong_keywords = [keyword for keyword in keywords if len(keyword) >= 4]
    hits = sum(1 for keyword in strong_keywords if keyword.casefold() in lower_text)
    return hits > 0


def _has_unsupported_specific_term(question: str, context_text: str, graph_context: str) -> bool:
    lower_question = question.casefold()
    combined_context = f"{context_text}\n{graph_context}".casefold()
    unsupported_terms = ["thú cưng", "chó", "mèo", "vật nuôi", "pet"]
    return any(term in lower_question and term not in combined_context for term in unsupported_terms)


def _normalize_fact_text(value: str) -> str:
    normalized = value.casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^\w\s./%-]", "", normalized, flags=re.UNICODE)
    return normalized.strip()


def _extract_fact_value(fact: RelationshipFact) -> str:
    text = f"{fact.target} {fact.description}"
    amount_match = re.search(
        r"\d[\d.,]*\s*(?:vnd|đ|dong|triệu|trieu|tỷ|ty|ngày|ngay|tháng|thang|năm|nam)",
        text,
        flags=re.IGNORECASE,
    )
    if amount_match:
        return _normalize_fact_text(amount_match.group(0))
    return _normalize_fact_text(fact.target)


def _fact_category(fact: RelationshipFact) -> str:
    target = _normalize_fact_text(fact.target)
    description = _normalize_fact_text(fact.description)
    combined = f"{target} {description}"
    category_source = _normalize_fact_text(fact.target)
    category_source = re.sub(
        r"\d[\d.,]*\s*(?:vnd|đ|dong|triệu|trieu|tỷ|ty|ngày|ngay|tháng|thang|năm|nam)(?:/\w+)?",
        "",
        category_source,
        flags=re.IGNORECASE,
    )
    category_source = re.sub(r"\d[\d.,]*", "", category_source).strip()
    if any(term in combined for term in ("vnd", "đ", "dong", "triệu", "trieu", "tỷ", "ty")):
        return category_source or "money_limit"
    if any(term in combined for term in ("ngày", "ngay", "tháng", "thang", "năm", "nam")):
        return category_source or "time_limit"
    return target


def detect_relationship_conflict(
    facts: list[RelationshipFact],
    *,
    allowed_relationship_types: set[str] | None = None,
) -> tuple[bool, str | None]:
    grouped_values: dict[tuple[str, str, str], set[str]] = {}
    for fact in facts:
        relationship_type = _normalize_fact_text(fact.relationship_type)
        if relationship_type not in CONFLICT_RELATIONSHIP_TYPES:
            continue
        if allowed_relationship_types is not None and relationship_type not in allowed_relationship_types:
            continue

        key = (
            _normalize_fact_text(fact.source),
            relationship_type,
            _fact_category(fact),
        )
        value = _extract_fact_value(fact)
        if not key[0] or not value:
            continue
        grouped_values.setdefault(key, set()).add(value)

    for (source, relationship_type, category), values in grouped_values.items():
        if len(values) > 1:
            return (
                True,
                (
                    "Mau thuan quan he Graph RAG: "
                    f"source={source}, relationship_type={relationship_type}, "
                    f"category={category}, values={sorted(values)}"
                ),
            )
    return False, None


def _conflict_relationship_types_for_question(question: str) -> set[str]:
    normalized = _normalize_fact_text(question)
    limit_terms = (
        "hạn mức",
        "han muc",
        "giới hạn",
        "gioi han",
        "bao nhiêu",
        "bao nhieu",
        "số tiền",
        "so tien",
        "vnd",
        "đồng",
        "dong",
        "tối đa",
        "toi da",
        "thời gian",
        "thoi gian",
        "bao lâu",
        "bao lau",
        "sla",
    )
    if any(term in normalized for term in limit_terms):
        return {"has_limit", "has_waiting_period", "payment_rule"}
    return set()


def _is_pet_question(question: str) -> bool:
    normalized = _normalize_fact_text(question)
    return any(term in normalized for term in ("thú cưng", "thu cung", "vật nuôi", "vat nuoi", "chó", "cho", "mèo", "meo", "pet"))


def _relationship_facts(relationships: list[RagRelationship]) -> list[RelationshipFact]:
    return [
        RelationshipFact(
            source=relationship.source_entity.name,
            relationship_type=relationship.relationship_type,
            target=relationship.target_entity.name,
            description=relationship.description or "",
        )
        for relationship in relationships
    ]


def _question_token_set(question: str) -> set[str]:
    return {
        token for token in _tokens(question)
        if len(token) >= 3 and token.casefold() not in QUERY_STOPWORDS
    }


def _text_overlap_score(question_tokens: set[str], text: str) -> float:
    if not question_tokens:
        return 0.0
    text_tokens = set(_tokens(text))
    if not text_tokens:
        return 0.0
    return min(1.0, len(question_tokens & text_tokens) / max(1, min(len(question_tokens), 6)))


def _entity_match_score(question: str, entities: list[RagEntity]) -> float:
    question_tokens = _question_token_set(question)
    if not entities:
        return 0.0
    best = 0.0
    for entity in entities:
        best = max(best, _text_overlap_score(question_tokens, f"{entity.name} {entity.description}"))
    return round(best, 4)


def _relationship_match_score(question: str, relationships: list[RagRelationship]) -> float:
    question_tokens = _question_token_set(question)
    if not relationships:
        return 0.0
    best = 0.0
    for relationship in relationships:
        text = (
            f"{relationship.source_entity.name} {relationship.relationship_type} "
            f"{relationship.target_entity.name} {relationship.description}"
        )
        best = max(best, _text_overlap_score(question_tokens, text))
    return round(best, 4)


def _filter_relationships_for_query(
    relationships: list[RagRelationship],
    *,
    classification: str,
    question: str,
) -> list[RagRelationship]:
    allowed_types = _allowed_relationship_types(classification, question)
    if not allowed_types:
        return []
    question_tokens = _question_token_set(question)
    normalized_question = _normalize_fact_text(question)
    asks_specific_benefit = any(
        term in normalized_question
        for term in (
            "tai nạn",
            "tai nan",
            "phẫu thuật",
            "phau thuat",
            "nội trú",
            "noi tru",
            "đua xe",
            "dua xe",
            "cứu hộ",
            "cuu ho",
        )
    )
    ranked: list[tuple[float, RagRelationship]] = []
    for relationship in relationships:
        if relationship.relationship_type not in allowed_types:
            continue
        source_score = _text_overlap_score(question_tokens, relationship.source_entity.name)
        target_score = _text_overlap_score(question_tokens, relationship.target_entity.name)
        if asks_specific_benefit and relationship.relationship_type == "covers" and target_score == 0:
            continue
        if source_score == 0 and target_score == 0:
            continue
        text = (
            f"{relationship.source_entity.name} {relationship.relationship_type} "
            f"{relationship.target_entity.name} {relationship.description}"
        )
        score = _text_overlap_score(question_tokens, text) + 0.35 * target_score + 0.2 * source_score
        ranked.append((score, relationship))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [relationship for _, relationship in ranked[:TOP_K_RELATIONSHIPS]]


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
        classification = classify_query(question)
        if classification == "unsupported":
            logger.debug(
                "Graph RAG retrieval",
                extra={
                    "question": question,
                    "classification": classification,
                    "confidence": 0.0,
                    "matched_entities": [],
                    "retrieved_chunks": [],
                },
            )
            return GraphRetrievalResult(
                chunks=[],
                matched_entities=[],
                relationships=[],
                context_text="",
                graph_context="",
                confidence_score=0.0,
                fallback_reason=UNSUPPORTED_QUERY_REASON,
                classification=classification,
            )

        keywords = _keywords(question)
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

        matched_entities = RagEntityRepository.search_entities(
            db,
            keywords=keywords,
            limit=20,
        )
        relationships = RagRelationshipRepository.list_connected(
            db,
            entity_ids=[entity.id for entity in matched_entities],
            limit=40,
        )
        relationships = _filter_relationships_for_query(
            relationships,
            classification=classification,
            question=question,
        )

        graph_chunk_ids = {
            relationship.chunk_id for relationship in relationships if relationship.chunk_id
        } | {entity.chunk_id for entity in matched_entities if entity.chunk_id}
        graph_document_ids = {
            relationship.document_id for relationship in relationships
        } | {entity.document_id for entity in matched_entities}

        relevant_chunks: list[RetrievedChunk] = []
        current_chunk_ids: set[int] = set()

        for item in scored:
            is_vector_hit = item.score >= settings.RAG_MIN_SCORE
            is_graph_hit = item.chunk.id in graph_chunk_ids
            is_same_document_graph_hit = item.chunk.document_id in graph_document_ids
            is_keyword_hit = _chunk_matches_question(item.chunk.content, keywords)
            if is_graph_hit or (
                is_vector_hit and (is_keyword_hit or is_same_document_graph_hit)
            ):
                relevant_chunks.append(item)
                current_chunk_ids.add(item.chunk.id)
            if len(relevant_chunks) >= TOP_K_CHUNKS:
                break

        chunk_entities = RagEntityRepository.list_by_chunk_ids(
            db,
            [item.chunk.id for item in relevant_chunks],
        )
        entity_by_id = {entity.id: entity for entity in matched_entities + chunk_entities}
        question_tokens = _question_token_set(question)
        ranked_entities = sorted(
            (
                (
                    _text_overlap_score(
                        question_tokens,
                        f"{entity.name} {entity.description}",
                    ),
                    entity,
                )
                for entity in entity_by_id.values()
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        matched_entities = [
            entity for score, entity in ranked_entities
            if score > 0
        ][:20]

        if matched_entities and not relationships:
            relationships = RagRelationshipRepository.list_connected(
                db,
                entity_ids=[entity.id for entity in matched_entities],
                limit=40,
            )
            relationships = _filter_relationships_for_query(
                relationships,
                classification=classification,
                question=question,
            )

        best_chunk_score = max((item.score for item in relevant_chunks), default=0.0)
        chunk_similarity_score = round(min(1.0, best_chunk_score), 4)
        entity_match_score = _entity_match_score(question, matched_entities)
        relationship_match_score = _relationship_match_score(question, relationships)
        confidence_score = round(
            min(
                1.0,
                0.45 * chunk_similarity_score
                + 0.35 * entity_match_score
                + 0.20 * relationship_match_score,
            ),
            4,
        )

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
                    for entity in matched_entities[:25]
                ],
                "Quan hệ nghiệp vụ:",
                *[
                    (
                        f"- {relationship.source_entity.name} "
                        f"--{relationship.relationship_type}--> "
                        f"{relationship.target_entity.name}: {relationship.description}"
                    )
                    for relationship in relationships[:TOP_K_RELATIONSHIPS]
                ],
            ]
        )

        conflict_relationship_types = _conflict_relationship_types_for_question(question)
        conflict_detected, conflict_reason = detect_relationship_conflict(
            _relationship_facts(relationships),
            allowed_relationship_types=conflict_relationship_types,
        )

        fallback_reason = None
        if not relevant_chunks and not matched_entities:
            fallback_reason = "Không tìm thấy đoạn tài liệu hoặc thực thể phù hợp."
            confidence_score = 0.0
        elif _is_pet_question(question) or _has_unsupported_specific_term(
            question,
            context_text,
            graph_context,
        ):
            fallback_reason = "Câu hỏi có chủ đề cụ thể không xuất hiện trong tài liệu nội bộ."
            confidence_score = 0.0
        elif conflict_detected:
            fallback_reason = CONFLICT_REFUSAL_REASON
            confidence_score = 0.0
        elif confidence_score < MIN_GRAPH_RAG_CONFIDENCE:
            fallback_reason = LOW_CONFIDENCE_REASON

        logger.debug(
            "Graph RAG retrieval",
            extra={
                "question": question,
                "classification": classification,
                "confidence": confidence_score,
                "entity_match_score": entity_match_score,
                "relationship_match_score": relationship_match_score,
                "chunk_similarity_score": chunk_similarity_score,
                "matched_entities": [entity.name for entity in matched_entities[:20]],
                "retrieved_relationships": [
                    (
                        f"{relationship.source_entity.name} "
                        f"--{relationship.relationship_type}--> "
                        f"{relationship.target_entity.name}"
                    )
                    for relationship in relationships[:40]
                ],
                "retrieved_chunks": [item.chunk.id for item in relevant_chunks],
                "retrieved_chunks_count": len(relevant_chunks),
                "conflict_detected": conflict_detected,
                "conflict_reason": conflict_reason,
            },
        )
        return GraphRetrievalResult(
            chunks=relevant_chunks,
            matched_entities=matched_entities,
            relationships=relationships,
            context_text=context_text,
            graph_context=graph_context,
            confidence_score=confidence_score,
            fallback_reason=fallback_reason,
            classification=classification,
            entity_match_score=entity_match_score,
            relationship_match_score=relationship_match_score,
            chunk_similarity_score=chunk_similarity_score,
        )
