import json
from typing import Any

import httpx

from app.core.config import settings

REFUSAL_MESSAGE = (
    "Xin lỗi, thông tin này chưa có trong tài liệu nội bộ của công ty. "
    "Vui lòng liên hệ nhân viên phụ trách để được hỗ trợ thêm."
)


class GeminiService:
    @staticmethod
    def is_configured() -> bool:
        return settings.AI_PROVIDER.lower() == "gemini" and bool(settings.GEMINI_API_KEY)

    @staticmethod
    def generate_text(prompt: str, *, temperature: float = 0.1) -> str | None:
        if not GeminiService.is_configured():
            return None

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.8,
                "maxOutputTokens": 1200,
            },
        }
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    url,
                    params={"key": settings.GEMINI_API_KEY},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError):
            return None

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, TypeError):
            return None

    @staticmethod
    def generate_json(prompt: str) -> dict[str, Any] | None:
        text = GeminiService.generate_text(prompt, temperature=0.0)
        if not text:
            return None
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
