import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.rag import DocumentChunk, RagEntity
from app.repositories.rag_repository import RagEntityRepository, RagRelationshipRepository
from app.services.gemini_service import GeminiService


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
    ("bảo hiểm sức khỏe", "insurance_package"),
    ("bảo hiểm xe máy", "insurance_package"),
    ("bảo hiểm ô tô", "insurance_package"),
    ("bảo hiểm nhà", "insurance_package"),
    ("bảo hiểm du lịch", "insurance_package"),
    ("bảo hiểm nhân thọ", "insurance_package"),
    ("quyền lợi", "benefit"),
    ("viện phí", "benefit"),
    ("phẫu thuật", "benefit"),
    ("cấp cứu", "benefit"),
    ("điều khoản loại trừ", "exclusion"),
    ("loại trừ", "exclusion"),
    ("hồ sơ bồi thường", "claim_process"),
    ("bồi thường", "claim_process"),
    ("giấy ra viện", "document_requirement"),
    ("hóa đơn", "document_requirement"),
    ("đơn thuốc", "document_requirement"),
    ("giấy tờ tùy thân", "document_requirement"),
    ("biên bản công an", "document_requirement"),
    ("thanh toán", "payment"),
    ("hạn mức", "time_limit"),
    ("hotline", "contact_channel"),
    ("chat", "contact_channel"),
]


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_with_gemini(chunk_text: str) -> tuple[list[ExtractedEntity], list[ExtractedRelationship]] | None:
    prompt = f"""
You are extracting a knowledge graph from an insurance company document.
Return JSON only.

Extract:
- entities
- relationships

Entity fields:
- name
- entity_type
- description

Relationship fields:
- source
- target
- relationship_type
- description

Allowed entity_type examples:
insurance_package, benefit, condition, exclusion, claim_process, document_requirement, hospital, vehicle, payment, time_limit, contact_channel

Allowed relationship_type examples:
includes, requires, excludes, applies_to, has_limit, has_waiting_period, needs_document, handled_by, related_to

Do not invent information.
Only extract what appears in the text.

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
        entity_type = _clean(str(item.get("entity_type", "related_to")))
        if name and entity_type:
            entities.append(
                ExtractedEntity(
                    name=name[:255],
                    entity_type=entity_type[:80],
                    description=_clean(str(item.get("description", "")))[:1000],
                )
            )

    relationships: list[ExtractedRelationship] = []
    for item in data.get("relationships", []):
        if not isinstance(item, dict):
            continue
        source = _clean(str(item.get("source", "")))
        target = _clean(str(item.get("target", "")))
        relationship_type = _clean(str(item.get("relationship_type", "related_to")))
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


def _extract_locally(chunk_text: str) -> tuple[list[ExtractedEntity], list[ExtractedRelationship]]:
    lower_text = chunk_text.lower()
    entities: list[ExtractedEntity] = []
    seen: set[str] = set()

    for keyword, entity_type in ENTITY_KEYWORDS:
        if keyword in lower_text and keyword not in seen:
            seen.add(keyword)
            sentence = next(
                (part.strip() for part in re.split(r"(?<=[.!?])\s+", chunk_text) if keyword in part.lower()),
                chunk_text[:220],
            )
            entities.append(
                ExtractedEntity(
                    name=keyword.title(),
                    entity_type=entity_type,
                    description=sentence[:1000],
                )
            )

    relationships: list[ExtractedRelationship] = []
    packages = [entity for entity in entities if entity.entity_type == "insurance_package"]
    requirements = [entity for entity in entities if entity.entity_type == "document_requirement"]
    benefits = [entity for entity in entities if entity.entity_type == "benefit"]
    exclusions = [entity for entity in entities if entity.entity_type == "exclusion"]
    processes = [entity for entity in entities if entity.entity_type == "claim_process"]

    for package in packages:
        for benefit in benefits:
            relationships.append(
                ExtractedRelationship(
                    source=package.name,
                    target=benefit.name,
                    relationship_type="includes",
                    description=f"{package.name} bao gồm hoặc liên quan đến {benefit.name}.",
                )
            )
        for exclusion in exclusions:
            relationships.append(
                ExtractedRelationship(
                    source=package.name,
                    target=exclusion.name,
                    relationship_type="excludes",
                    description=f"{package.name} có nội dung loại trừ liên quan đến {exclusion.name}.",
                )
            )
    for process in processes:
        for requirement in requirements:
            relationships.append(
                ExtractedRelationship(
                    source=process.name,
                    target=requirement.name,
                    relationship_type="needs_document",
                    description=f"{process.name} cần chứng từ {requirement.name}.",
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
    def extract_chunk_graph(chunk_text: str) -> tuple[list[ExtractedEntity], list[ExtractedRelationship]]:
        return _extract_with_gemini(chunk_text) or _extract_locally(chunk_text)

    @staticmethod
    def ingest_chunk(db: Session, *, chunk: DocumentChunk) -> None:
        extracted_entities, extracted_relationships = GraphRagIngestionService.extract_chunk_graph(
            chunk.content
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
            source = entity_by_name.get(item.source.casefold())
            target = entity_by_name.get(item.target.casefold())
            if source is None or target is None or source.id == target.id:
                continue
            RagRelationshipRepository.create_relationship(
                db,
                source_entity_id=source.id,
                target_entity_id=target.id,
                relationship_type=item.relationship_type,
                description=item.description or f"{source.name} liên quan đến {target.name}.",
                document_id=chunk.document_id,
                chunk_id=chunk.id,
            )

    @staticmethod
    def ingest_chunks(db: Session, *, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            GraphRagIngestionService.ingest_chunk(db, chunk=chunk)
