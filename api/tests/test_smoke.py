from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import LoginRequest
from app.services.graph_rag_retrieval_service import (
    RelationshipFact,
    classify_query,
    detect_relationship_conflict,
)
from app.services.rag_service import LocalEmbeddingService, _cosine_score


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_schema_accepts_local_demo_email() -> None:
    payload = LoginRequest(email="admin@insurance.local", password="11111111")

    assert payload.email == "admin@insurance.local"


def test_local_embedding_scores_related_text_higher() -> None:
    service = LocalEmbeddingService()
    query = service.embed("health insurance coverage")
    related = service.embed("health insurance package coverage details")
    unrelated = service.embed("appointment chat schedule")

    assert _cosine_score(query, related) > _cosine_score(query, unrelated)


def test_graph_rag_cover_and_exclusion_are_not_conflict() -> None:
    facts = [
        RelationshipFact(
            source="Bảo hiểm xe máy",
            relationship_type="covers",
            target="Tai nạn xe máy",
        ),
        RelationshipFact(
            source="Bảo hiểm xe máy",
            relationship_type="excludes",
            target="Đua xe",
        ),
    ]

    conflict_detected, conflict_reason = detect_relationship_conflict(facts)

    assert conflict_detected is False
    assert conflict_reason is None


def test_graph_rag_different_limits_are_conflict() -> None:
    facts = [
        RelationshipFact(
            source="Bảo hiểm xe máy",
            relationship_type="has_limit",
            target="30.000.000 VND/năm",
        ),
        RelationshipFact(
            source="Bảo hiểm xe máy",
            relationship_type="has_limit",
            target="50.000.000 VND/năm",
        ),
    ]

    conflict_detected, conflict_reason = detect_relationship_conflict(facts)

    assert conflict_detected is True
    assert conflict_reason is not None


def test_graph_rag_query_classification_blocks_irrelevant_questions() -> None:
    assert classify_query("Tôi là ai?") == "unsupported"
    assert classify_query("Bạn là ai?") == "unsupported"
    assert classify_query("Giá bitcoin là bao nhiêu?") == "unsupported"


def test_graph_rag_query_classification_accepts_insurance_questions() -> None:
    assert classify_query("Bảo hiểm xe máy có hỗ trợ tai nạn không?") == "insurance_knowledge"
    assert classify_query("Hồ sơ bồi thường cần giấy tờ gì?") == "claim_process"
