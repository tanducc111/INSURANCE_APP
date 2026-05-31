from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import LoginRequest
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
