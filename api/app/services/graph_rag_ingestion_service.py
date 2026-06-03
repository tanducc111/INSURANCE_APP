import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.rag import DocumentChunk, RagEntity
from app.repositories.rag_repository import (
    RagEntityRepository,
    RagRelationshipRepository,
)
from app.services.gemini_service import GeminiService


ALLOWED_ENTITY_TYPES = {
    "insurance_package",
    "benefit",
    "coverage_limit",
    "claim_document",
    "claim_process",
    "claim_status",
    "exclusion",
    "condition",
    "payment_rule",
    "support_channel",
    "next_action",
    "role",
}

ALLOWED_RELATIONSHIP_TYPES = {
    "covers",
    "requires",
    "excludes",
    "has_limit",
    "applies_to",
    "needs_document",
    "next_action",
    "handled_by",
    "related_to",
}


@dataclass
class ExtractedEntity:
    name: str
    entity_type: str
    description: str


@dataclass
class ExtractedRelationship:
    source: str
    target: str
    relationship_type: str
    description: str


ENTITY_KEYWORDS: list[tuple[str, str]] = [
    ("Bảo hiểm xe máy", "insurance_package"),
    ("Bảo hiểm ô tô", "insurance_package"),
    ("Bảo hiểm sức khỏe cao cấp", "insurance_package"),
    ("Bảo hiểm sức khỏe", "insurance_package"),
    ("Bảo hiểm nhà ở", "insurance_package"),
    ("Tai nạn xe máy", "benefit"),
    ("Phẫu thuật", "benefit"),
    ("Điều trị nội trú", "benefit"),
    ("Cứu hộ kéo xe", "benefit"),
    ("Hóa đơn sửa chữa", "claim_document"),
    ("Biên lai sửa chữa", "claim_document"),
    ("Hình ảnh hiện trường", "claim_document"),
    ("Biên bản công an", "claim_document"),
    ("Giấy ra viện", "claim_document"),
    ("Hóa đơn viện phí", "claim_document"),
    ("Hồ sơ bồi thường", "claim_process"),
    ("Cần bổ sung hồ sơ", "claim_status"),
    ("Chờ xử lý", "claim_status"),
    ("Đang xem xét", "claim_status"),
    ("Đã duyệt", "claim_status"),
    ("Từ chối", "claim_status"),
    ("Hoàn tất", "claim_status"),
    ("Thanh toán bồi thường", "payment_rule"),
    ("Khách hàng bổ sung chứng từ", "next_action"),
    ("Đua xe", "exclusion"),
    ("Sử dụng xe trái phép", "exclusion"),
    ("Cố ý gây ra tai nạn", "exclusion"),
    ("Nhân viên phụ trách", "role"),
    ("Hotline", "support_channel"),
    ("Trò chuyện", "support_channel"),
]

STATUS_ACTIONS = {
    "Cần bổ sung hồ sơ": "Khách hàng bổ sung chứng từ",
    "Đã duyệt": "Thanh toán bồi thường",
    "Chờ xử lý": "Nhân viên xác nhận tiếp nhận hồ sơ",
    "Đang xem xét": "Nhân viên thẩm định hồ sơ",
}


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_entity_type(value: str) -> str:
    value = _clean(value)
    aliases = {
        "document_requirement": "claim_document",
        "payment": "payment_rule",
        "time_limit": "coverage_limit",
        "contact_channel": "support_channel",
    }
    value = aliases.get(value, value)
    return value if value in ALLOWED_ENTITY_TYPES else "condition"


def _normalize_relationship_type(value: str) -> str:
    value = _clean(value)
    aliases = {
        "includes": "covers",
        "has_waiting_period": "has_limit",
    }
    value = aliases.get(value, value)
    return value if value in ALLOWED_RELATIONSHIP_TYPES else "related_to"


def _extract_with_gemini(
    chunk_text: str,
) -> tuple[list[ExtractedEntity], list[ExtractedRelationship]] | None:
    prompt = f"""
You are extracting a knowledge graph from an official Vietnamese insurance company document.
Return valid JSON only. Do not include markdown.

Extract only facts explicitly present in the text.
Do not invent benefits, limits, exclusions, conditions, required documents, roles, or next actions.

Allowed entity_type values:
- insurance_package
- benefit
- coverage_limit
- claim_document
- claim_process
- claim_status
- exclusion
- condition
- payment_rule
- support_channel
- next_action
- role

Allowed relationship_type values:
- covers
- requires
- excludes
- has_limit
- applies_to
- needs_document
- next_action
- handled_by
- related_to

Return JSON with this shape:
{{
  "entities": [
    {{"name": "...", "entity_type": "...", "description": "..."}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "relationship_type": "...", "description": "..."}}
  ]
}}

Examples:
- "Bảo hiểm xe máy requires Hình ảnh hiện trường"
- "Bảo hiểm xe máy requires Hóa đơn sửa chữa"
- "Bảo hiểm xe máy excludes Đua xe"
- "Bảo hiểm xe máy has_limit 30.000.000 VND/năm"
- "Cần bổ sung hồ sơ next_action Khách hàng bổ sung chứng từ"
- "Đã duyệt next_action Thanh toán bồi thường"

Text:
{chunk_text}
"""
    data = GeminiService.generate_json(prompt)
    if not data:
        return None

    entities: list[ExtractedEntity] = []
    for item in data.get("entities", []):
        if not isinstance(item, dict):
            continue
        name = _clean(str(item.get("name", "")))
        entity_type = _normalize_entity_type(str(item.get("entity_type", "")))
        if name:
            entities.append(
                ExtractedEntity(
                    name=name[:255],
                    entity_type=entity_type[:80],
                    description=_clean(str(item.get("description", "")))[:1000] or name[:255],
                )
            )

    relationships: list[ExtractedRelationship] = []
    for item in data.get("relationships", []):
        if not isinstance(item, dict):
            continue
        source = _clean(str(item.get("source", "")))
        target = _clean(str(item.get("target", "")))
        relationship_type = _normalize_relationship_type(
            str(item.get("relationship_type", "related_to"))
        )
        if source and target:
            relationships.append(
                ExtractedRelationship(
                    source=source[:255],
                    target=target[:255],
                    relationship_type=relationship_type[:80],
                    description=_clean(str(item.get("description", "")))[:1000],
                )
            )
    return entities, relationships


def _add_entity(
    entities: list[ExtractedEntity],
    seen: set[str],
    *,
    name: str,
    entity_type: str,
    description: str,
) -> None:
    key = name.casefold()
    if key in seen:
        return
    seen.add(key)
    entities.append(
        ExtractedEntity(
            name=name[:255],
            entity_type=entity_type,
            description=_clean(description)[:1000] or name,
        )
    )


def _extract_limit_entities(
    chunk_text: str,
    entities: list[ExtractedEntity],
    seen: set[str],
) -> list[str]:
    limits = re.findall(
        r"\b\d{1,3}(?:[.,]\d{3})*(?:\s?VND|\s?đồng)(?:/[^\s,.]+)?",
        chunk_text,
        flags=re.IGNORECASE,
    )
    normalized_limits: list[str] = []
    for limit in limits:
        name = _clean(limit)
        normalized_limits.append(name)
        _add_entity(
            entities,
            seen,
            name=name,
            entity_type="coverage_limit",
            description=f"Hạn mức hoặc số tiền được nêu trong tài liệu: {name}.",
        )
    return normalized_limits


def _extract_locally(
    chunk_text: str,
) -> tuple[list[ExtractedEntity], list[ExtractedRelationship]]:
    lower_text = chunk_text.casefold()
    entities: list[ExtractedEntity] = []
    seen: set[str] = set()

    for keyword, entity_type in ENTITY_KEYWORDS:
        if keyword.casefold() in lower_text:
            sentence = next(
                (
                    part.strip()
                    for part in re.split(r"(?<=[.!?])\s+", chunk_text)
                    if keyword.casefold() in part.casefold()
                ),
                chunk_text[:240],
            )
            _add_entity(
                entities,
                seen,
                name=keyword,
                entity_type=entity_type,
                description=sentence,
            )

    limits = _extract_limit_entities(chunk_text, entities, seen)
    packages = [entity for entity in entities if entity.entity_type == "insurance_package"]
    benefits = [entity for entity in entities if entity.entity_type == "benefit"]
    documents = [entity for entity in entities if entity.entity_type == "claim_document"]
    exclusions = [entity for entity in entities if entity.entity_type == "exclusion"]
    statuses = [entity for entity in entities if entity.entity_type == "claim_status"]

    relationships: list[ExtractedRelationship] = []
    for package in packages:
        for benefit in benefits:
            relationships.append(
                ExtractedRelationship(
                    source=package.name,
                    target=benefit.name,
                    relationship_type="covers",
                    description=f"{package.name} có quyền lợi liên quan đến {benefit.name}.",
                )
            )
        for document in documents:
            relationships.append(
                ExtractedRelationship(
                    source=package.name,
                    target=document.name,
                    relationship_type="requires",
                    description=f"{package.name} yêu cầu hoặc liên quan đến chứng từ {document.name}.",
                )
            )
        for exclusion in exclusions:
            relationships.append(
                ExtractedRelationship(
                    source=package.name,
                    target=exclusion.name,
                    relationship_type="excludes",
                    description=f"{package.name} loại trừ trường hợp {exclusion.name}.",
                )
            )
        for limit in limits:
            relationships.append(
                ExtractedRelationship(
                    source=package.name,
                    target=limit,
                    relationship_type="has_limit",
                    description=f"{package.name} có hạn mức được nêu là {limit}.",
                )
            )

    for status_entity in statuses:
        action = STATUS_ACTIONS.get(status_entity.name)
        if not action:
            continue
        _add_entity(
            entities,
            seen,
            name=action,
            entity_type="next_action",
            description=f"Hành động tiếp theo khi hồ sơ ở trạng thái {status_entity.name}.",
        )
        relationships.append(
            ExtractedRelationship(
                source=status_entity.name,
                target=action,
                relationship_type="next_action",
                description=f"Khi hồ sơ ở trạng thái {status_entity.name}, hành động tiếp theo là {action}.",
            )
        )

    if "hồ sơ bồi thường" in lower_text:
        for document in documents:
            relationships.append(
                ExtractedRelationship(
                    source="Hồ sơ bồi thường",
                    target=document.name,
                    relationship_type="needs_document",
                    description=f"Hồ sơ bồi thường cần chứng từ {document.name}.",
                )
            )

    if not relationships and len(entities) >= 2:
        relationships.append(
            ExtractedRelationship(
                source=entities[0].name,
                target=entities[1].name,
                relationship_type="related_to",
                description="Hai khái niệm cùng xuất hiện trong một đoạn tài liệu.",
            )
        )
    return entities, relationships


class GraphRagIngestionService:
    @staticmethod
    def extract_chunk_graph(
        chunk_text: str,
    ) -> tuple[list[ExtractedEntity], list[ExtractedRelationship]]:
        return _extract_with_gemini(chunk_text) or _extract_locally(chunk_text)

    @staticmethod
    def ingest_chunk(db: Session, *, chunk: DocumentChunk) -> None:
        extracted_entities, extracted_relationships = (
            GraphRagIngestionService.extract_chunk_graph(chunk.content)
        )
        entity_by_name: dict[str, RagEntity] = {}
        for item in extracted_entities:
            key = item.name.casefold()
            if key in entity_by_name:
                continue
            entity = RagEntityRepository.create_entity(
                db,
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                name=item.name,
                entity_type=item.entity_type,
                description=item.description or item.name,
            )
            entity_by_name[key] = entity
        db.flush()

        for item in extracted_relationships:
            for name in (item.source, item.target):
                key = name.casefold()
                if key in entity_by_name:
                    continue
                entity = RagEntityRepository.create_entity(
                    db,
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    name=name,
                    entity_type="condition",
                    description=f"Khái niệm được trích xuất từ quan hệ trong tài liệu: {name}.",
                )
                entity_by_name[key] = entity
            db.flush()

            source = entity_by_name.get(item.source.casefold())
            target = entity_by_name.get(item.target.casefold())
            if source is None or target is None or source.id == target.id:
                continue
            RagRelationshipRepository.create_relationship(
                db,
                source_entity_id=source.id,
                target_entity_id=target.id,
                relationship_type=item.relationship_type,
                description=(
                    item.description
                    or f"{source.name} liên quan đến {target.name}."
                ),
                document_id=chunk.document_id,
                chunk_id=chunk.id,
            )

    @staticmethod
    def ingest_chunks(db: Session, *, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            GraphRagIngestionService.ingest_chunk(db, chunk=chunk)
