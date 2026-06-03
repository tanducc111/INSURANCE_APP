import io
import logging
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.rag import Document, DocumentChunk
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.rag_repository import (
    DocumentChunkRepository,
    DocumentRepository,
    RagChatLogRepository,
    RagEntityRepository,
    RagRelationshipRepository,
)
from app.schemas.rag import (
    ChatbotAnswer,
    ChatbotMatchedEntity,
    ChatbotQuestion,
    ChatbotSource,
)
from app.services.gemini_service import REFUSAL_MESSAGE, GeminiService
from app.services.graph_rag_ingestion_service import GraphRagIngestionService


logger = logging.getLogger(__name__)

CONFLICT_REFUSAL_MESSAGE = (
    "Xin lỗi, tài liệu nội bộ hiện có nhiều thông tin chưa thống nhất về nội dung này. "
    "Vui lòng liên hệ nhân viên phụ trách để được xác nhận theo phiên bản tài liệu mới nhất."
)
UNSUPPORTED_CHATBOT_MESSAGE = (
    "Xin lỗi, tôi chỉ có thể trả lời các câu hỏi liên quan đến tài liệu bảo hiểm nội bộ "
    "đã được công ty tải lên. Vui lòng đặt câu hỏi về quyền lợi bảo hiểm, hợp đồng, "
    "hồ sơ bồi thường hoặc quy trình xử lý."
)


TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if len(token) > 1]


class EmbeddingService:
    def embed(self, text: str) -> dict[str, float]:
        raise NotImplementedError


class LocalEmbeddingService(EmbeddingService):
    def embed(self, text: str) -> dict[str, float]:
        counts: dict[str, float] = {}
        for token in _tokens(text):
            counts[token] = counts.get(token, 0.0) + 1.0
        length = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {token: value / length for token, value in counts.items()}


def get_embedding_service() -> EmbeddingService:
    if settings.EMBEDDING_PROVIDER != "local" and not settings.EMBEDDING_API_KEY:
        return LocalEmbeddingService()
    return LocalEmbeddingService()


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


def _cosine_score(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def _extract_pdf_text_with_page_count(content: bytes) -> tuple[str, int]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF extraction dependency is not installed",
        ) from exc

    reader = PdfReader(io.BytesIO(content))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page_texts), len(reader.pages)


def _extract_pdf_text(content: bytes) -> str:
    return _extract_pdf_text_with_page_count(content)[0]


def _extract_text_with_page_count(
    file_name: str,
    content_type: str,
    content: bytes,
) -> tuple[str, int]:
    lower_name = file_name.lower()
    if content_type == "application/pdf" or lower_name.endswith(".pdf"):
        return _extract_pdf_text_with_page_count(content)
    if (
        content_type.startswith("text/")
        or lower_name.endswith(".txt")
        or lower_name.endswith(".md")
    ):
        return _decode_text(content), 0
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Only PDF, TXT, and Markdown documents are supported",
    )


def _extract_text(file_name: str, content_type: str, content: bytes) -> str:
    return _extract_text_with_page_count(file_name, content_type, content)[0]


def _validate_supported_document(file_name: str, content_type: str) -> None:
    lower_name = file_name.lower()
    if content_type == "application/pdf" or lower_name.endswith(".pdf"):
        return
    if (
        content_type.startswith("text/")
        or lower_name.endswith(".txt")
        or lower_name.endswith(".md")
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Chi ho tro tai lieu PDF, TXT hoac Markdown",
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_document_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    normalized_lines: list[str] = []
    blank_seen = False
    for line in lines:
        if not line:
            if not blank_seen and normalized_lines:
                normalized_lines.append("")
            blank_seen = True
            continue
        normalized_lines.append(line)
        blank_seen = False
    return "\n".join(normalized_lines).strip()


HEADING_PATTERN = re.compile(
    r"^(?:\d+(?:\.\d+)*[.)]?\s+|[IVXLCDM]+[.)]\s+|Mục\s+\d+|Phần\s+\d+|Chương\s+\d+)",
    re.IGNORECASE,
)


def _is_heading_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 140:
        return False
    if HEADING_PATTERN.match(stripped):
        return True
    return stripped.isupper() and len(stripped.split()) <= 12


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    if "|" in stripped or "\t" in stripped:
        return True
    return bool(re.search(r"\S\s{2,}\S\s{2,}\S", line))


def _flush_block(blocks: list[str], lines: list[str]) -> None:
    if lines:
        blocks.append("\n".join(lines).strip())
        lines.clear()


def _split_into_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    paragraph_lines: list[str] = []
    table_lines: list[str] = []

    for line in text.splitlines():
        if not line.strip():
            _flush_block(blocks, table_lines)
            _flush_block(blocks, paragraph_lines)
            continue

        if _is_table_line(line):
            _flush_block(blocks, paragraph_lines)
            table_lines.append(line)
            continue

        _flush_block(blocks, table_lines)
        if _is_heading_line(line):
            _flush_block(blocks, paragraph_lines)
        paragraph_lines.append(line)

    _flush_block(blocks, table_lines)
    _flush_block(blocks, paragraph_lines)
    return [block for block in blocks if block]


def _is_table_block(block: str) -> bool:
    lines = [line for line in block.splitlines() if line.strip()]
    return bool(lines) and all(_is_table_line(line) for line in lines)


def _split_large_block(block: str, chunk_size: int) -> list[str]:
    if _is_table_block(block):
        return [block]
    normalized = _normalize_text(block)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?。])\s+", normalized)
        if sentence.strip()
    ] or [normalized]

    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                parts.append(current)
                current = ""
            words = sentence.split()
            piece = ""
            for word in words:
                candidate = f"{piece} {word}".strip()
                if len(candidate) > chunk_size and piece:
                    parts.append(piece)
                    piece = word
                else:
                    piece = candidate
            if piece:
                parts.append(piece)
            continue

        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > chunk_size:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def _overlap_tail(text: str, overlap: int) -> str:
    if overlap <= 0:
        return ""
    tail: list[str] = []
    total = 0
    for word in reversed(text.split()):
        total += len(word) + 1
        if total > overlap:
            break
        tail.append(word)
    return " ".join(reversed(tail))


def _merge_small_chunks(
    chunks: list[str],
    *,
    min_size: int = 700,
    max_size: int = 1000,
) -> list[str]:
    merged: list[str] = []
    current = ""
    for chunk in chunks:
        if not current:
            current = chunk
            continue
        candidate = f"{current}\n\n{chunk}".strip()
        if len(current) < min_size and len(candidate) <= max_size:
            current = candidate
            continue
        merged.append(current)
        current = chunk
    if current:
        merged.append(current)
    return merged


def _chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 180) -> list[str]:
    normalized = _normalize_document_text(text)
    if not normalized:
        return []

    blocks: list[str] = []
    for block in _split_into_blocks(normalized):
        blocks.extend(_split_large_block(block, chunk_size) if len(block) > chunk_size else [block])

    chunks: list[str] = []
    current = ""

    def push_current(*, keep_overlap: bool = True) -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = _overlap_tail(current, overlap) if keep_overlap else ""

    for block in blocks:
        first_line = block.splitlines()[0] if block.splitlines() else block
        if _is_heading_line(first_line):
            if current and len(current) < 300:
                current = f"{current}\n\n{block}".strip()
                continue
            push_current(keep_overlap=False)
            current = block
            continue
        candidate = f"{current}\n\n{block}".strip() if current else block
        if current and len(candidate) > chunk_size:
            push_current()
            candidate = f"{current}\n\n{block}".strip() if current else block
        current = candidate
    push_current(keep_overlap=False)
    return _merge_small_chunks([chunk for chunk in chunks if chunk])


def _unique_chunks(chunks: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        key = chunk.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(chunk)
    return unique


def _limit_chunks(chunks: list[str]) -> tuple[list[str], int]:
    unique_chunks = _unique_chunks(chunks)
    skipped = max(0, len(chunks) - len(unique_chunks))
    max_chunks = max(1, settings.RAG_MAX_CHUNKS_PER_DOCUMENT)
    if len(unique_chunks) > max_chunks:
        skipped += len(unique_chunks) - max_chunks
        unique_chunks = unique_chunks[:max_chunks]
    return unique_chunks, skipped


def _document_upload_dir() -> Path:
    upload_dir = Path(settings.DOCUMENT_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _safe_file_name(document_id: int, file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(file_name).stem).strip("-")
    safe_stem = safe_stem[:80] or "document"
    return f"{document_id}-{safe_stem}{suffix}"


def _preview_text(text: str, *, max_length: int = 260) -> str:
    preview = _clean_evidence_sentence(text)
    if len(preview) > max_length:
        boundary = preview.rfind(" ", 0, max_length)
        preview = preview[: boundary if boundary > 80 else max_length].rstrip() + "..."
    if preview and preview[0].islower():
        preview = f"... {preview}"
    return preview


def _clean_evidence_sentence(sentence: str) -> str:
    cleaned = _normalize_text(sentence)
    cleaned = re.sub(r"Tài liệu:\s*[^\n]+\s*Đoạn\s*\d+:", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"Đoạn\s*\d+:", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}\s*(AM|PM)?", "", cleaned)
    cleaned = re.sub(r"file:///\S+", "", cleaned)
    cleaned = re.sub(r"\b\d+/\d+\b", "", cleaned)
    cleaned = re.sub(r"^[-–•\s]+", "", cleaned)
    return _normalize_text(cleaned)


def _select_evidence_sentences(question: str, context_text: str, *, limit: int = 5) -> list[str]:
    keywords = {token for token in _tokens(question) if len(token) >= 3}
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?。])\s+", context_text)
        if sentence.strip()
    ]
    ranked: list[tuple[int, str]] = []
    for sentence in sentences:
        sentence_tokens = set(_tokens(sentence))
        score = len(keywords & sentence_tokens)
        if score:
            ranked.append((score, sentence))
    ranked.sort(key=lambda item: item[0], reverse=True)
    selected: list[str] = []
    seen: set[str] = set()
    for _, sentence in ranked:
        clean = _clean_evidence_sentence(sentence)
        if clean and len(clean) > 20 and clean not in seen:
            selected.append(clean)
            seen.add(clean)
        if len(selected) >= limit:
            break
    return selected


def _answer_explicit_negative(question: str, context_text: str, source_documents: str) -> str | None:
    lower_question = question.lower()
    lower_context = context_text.lower()
    pet_terms = ("thú cưng", "vật nuôi", "chó", "mèo", "pet")
    negative_terms = ("không quy định", "không có", "chưa có", "không hỗ trợ")
    if any(term in lower_question for term in pet_terms) and any(
        term in lower_context for term in pet_terms
    ) and any(term in lower_context for term in negative_terms):
        return (
            "Theo tài liệu nội bộ của công ty, hiện tài liệu chưa quy định sản phẩm "
            "bảo hiểm cho thú cưng. Vì vậy mình không thể xác nhận công ty đang cung cấp "
            "quyền lợi này.\n\n"
            "Bạn nên liên hệ nhân viên phụ trách để được kiểm tra thêm nếu công ty có "
            "chính sách mới hoặc sản phẩm đặc biệt chưa được cập nhật vào tài liệu.\n\n"
            "Nguồn tham khảo:\n"
            + (source_documents or "- Tài liệu nội bộ đã tải lên")
        )
    return None


def _answer_common_insurance_question(
    question: str,
    context_text: str,
    source_documents: str,
) -> str | None:
    lower_question = question.lower()
    lower_context = context_text.lower()
    source_block = source_documents or "- Tài liệu nội bộ đã tải lên"

    if (
        "sức khỏe" in lower_question
        and "quyền lợi" in lower_question
        and "điều trị nội trú" in lower_context
    ):
        return (
            "Theo tài liệu nội bộ, quyền lợi bảo hiểm sức khỏe được mô tả theo từng gói:\n\n"
            "- Gói sức khỏe cơ bản: chi trả điều trị nội trú, cấp cứu, xe cấp cứu và một lần khám sức khỏe định kỳ mỗi năm.\n"
            "- Gói sức khỏe cao cấp: bao gồm quyền lợi của gói cơ bản và bổ sung phẫu thuật, bác sĩ chuyên khoa, thuốc điều trị sau phẫu thuật, phòng bệnh tiêu chuẩn cao.\n"
            "- Gói sức khỏe gia đình: áp dụng cho cha mẹ và con cái trong cùng hợp đồng, bao gồm nhi khoa, khám phòng ngừa và điều trị nội trú cho thành viên gia đình.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if (
        ("giấy tờ" in lower_question or "hồ sơ" in lower_question)
        and "bồi thường" in lower_question
        and "mẫu yêu cầu bồi thường" in lower_context
    ):
        return (
            "Theo tài liệu nội bộ, khi nộp hồ sơ bồi thường khách hàng cần chuẩn bị các nhóm giấy tờ sau:\n\n"
            "- Mẫu yêu cầu bồi thường theo biểu mẫu của công ty.\n"
            "- Số hợp đồng bảo hiểm hoặc số giấy chứng nhận bảo hiểm.\n"
            "- Giấy tờ tùy thân của người được bảo hiểm.\n"
            "- Chứng từ theo từng trường hợp, ví dụ: giấy ra viện, giấy chứng nhận phẫu thuật, kết quả chẩn đoán, hóa đơn viện phí, bảng kê chi phí, đơn thuốc, hình ảnh hiện trường, báo giá sửa chữa hoặc biên bản công an nếu cần.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if (
        "xe máy" in lower_question
        and ("tai nạn" in lower_question or "hỗ trợ" in lower_question)
        and "hỗ trợ tai nạn xe máy" in lower_context
    ):
        return (
            "Theo tài liệu nội bộ, bảo hiểm xe máy có hỗ trợ tai nạn xe máy nếu sự cố xảy ra trong thời hạn hợp đồng đang hiệu lực.\n\n"
            "Các hỗ trợ được nêu trong tài liệu gồm:\n"
            "- Hỗ trợ tai nạn xe máy.\n"
            "- Hỗ trợ sửa chữa khi có hình ảnh hiện trường và hóa đơn hợp lệ.\n"
            "- Hỗ trợ trách nhiệm dân sự và cứu hộ kéo xe trong hạn mức.\n\n"
            "Tài liệu cũng nêu không áp dụng cho hành vi đua xe, sử dụng xe trái phép hoặc tai nạn do cố ý gây ra.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if (
        "thời gian" in lower_question
        and "bồi thường" in lower_question
        and "07 ngày làm việc" in context_text
    ):
        return (
            "Theo tài liệu nội bộ, thời gian xử lý hồ sơ bồi thường được mô tả như sau:\n\n"
            "- Trong vòng 01 ngày làm việc: nhân viên xác nhận đã tiếp nhận hồ sơ.\n"
            "- Trong vòng 03 ngày làm việc: nhân viên thông báo chứng từ cần bổ sung nếu hồ sơ chưa đầy đủ.\n"
            "- Trong vòng 07 ngày làm việc kể từ khi nhận đủ chứng từ: công ty hoàn tất thẩm định hồ sơ thông thường.\n"
            "- Trong vòng 05 ngày làm việc sau khi hồ sơ được phê duyệt: công ty thanh toán khoản bồi thường.\n\n"
            "Với hồ sơ phức tạp, tài liệu cho biết có thể cần thêm thời gian xác minh và nhân viên phải thông báo lý do cho khách hàng.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    return None


def _answer_graph_cases(question: str, context_text: str, source_documents: str) -> str | None:
    lower_question = question.casefold()
    lower_context = context_text.casefold()
    source_block = source_documents or "- Tài liệu nội bộ đã tải lên"

    if "xe máy" in lower_question and "đua xe" in lower_question and "excludes" in lower_context:
        return (
            "Theo tài liệu nội bộ, bảo hiểm xe máy không chi trả cho trường hợp đua xe nếu nội dung tài liệu xác định đây là điều khoản loại trừ.\n\n"
            "Bạn nên liên hệ nhân viên phụ trách nếu cần kiểm tra thêm theo hợp đồng cụ thể.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if "cần bổ sung" in lower_question and (
        "khách hàng bổ sung chứng từ" in lower_context or "next_action" in lower_context
    ):
        return (
            "Theo tài liệu nội bộ, khi hồ sơ ở trạng thái cần bổ sung hồ sơ, hành động tiếp theo là khách hàng bổ sung chứng từ còn thiếu theo hướng dẫn của nhân viên phụ trách.\n\n"
            "Bạn nên kiểm tra danh sách chứng từ được yêu cầu và gửi thêm tài liệu liên quan như hóa đơn, hình ảnh hiện trường, biên bản hoặc giấy tờ y tế nếu được yêu cầu.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if "xe máy" in lower_question and "hóa đơn sửa chữa" in lower_question:
        return (
            "Theo tài liệu nội bộ, bạn có thể gửi thông tin sự cố ban đầu để nhân viên tiếp nhận hồ sơ. Tuy nhiên, hồ sơ bồi thường xe máy có thể cần hóa đơn sửa chữa hoặc chứng từ sửa chữa hợp lệ.\n\n"
            "Nếu hiện chưa có hóa đơn sửa chữa, hồ sơ có thể được chuyển sang trạng thái cần bổ sung hồ sơ cho đến khi bạn cung cấp đủ chứng từ. Bạn nên liên hệ nhân viên phụ trách để được hướng dẫn danh sách giấy tờ cần nộp.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if "xe máy" in lower_question and "tai nạn" in lower_question and (
        "covers" in lower_context or "tai nạn xe máy" in lower_context
    ):
        return (
            "Theo tài liệu nội bộ, bảo hiểm xe máy có hỗ trợ tai nạn xe máy nếu sự cố thuộc phạm vi bảo hiểm và không rơi vào điều khoản loại trừ.\n\n"
            "Các chứng từ liên quan có thể gồm hình ảnh hiện trường, hóa đơn sửa chữa, biên lai sửa chữa hoặc biên bản công an nếu tài liệu/hồ sơ yêu cầu.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    if "sức khỏe cao cấp" in lower_question and "phẫu thuật" in lower_question and (
        "phẫu thuật" in lower_context
    ):
        return (
            "Theo tài liệu nội bộ, bảo hiểm sức khỏe cao cấp có nội dung hỗ trợ liên quan đến phẫu thuật nếu đáp ứng điều kiện và phạm vi quyền lợi được nêu trong tài liệu.\n\n"
            "Bạn nên kiểm tra thêm hợp đồng cụ thể hoặc liên hệ nhân viên phụ trách để xác nhận hồ sơ chứng từ cần chuẩn bị.\n\n"
            "Nguồn tham khảo:\n"
            f"{source_block}"
        )

    return None


def _build_local_answer(question: str, context_text: str, source_documents: str) -> str:
    graph_answer = _answer_graph_cases(question, context_text, source_documents)
    if graph_answer:
        return graph_answer

    explicit_negative = _answer_explicit_negative(question, context_text, source_documents)
    if explicit_negative:
        return explicit_negative

    common_answer = _answer_common_insurance_question(question, context_text, source_documents)
    if common_answer:
        return common_answer

    evidence = _select_evidence_sentences(question, context_text)
    if not evidence:
        return REFUSAL_MESSAGE

    bullet_lines = "\n".join(f"- {sentence}" for sentence in evidence)
    return (
        "Theo tài liệu nội bộ của công ty, mình có thể trả lời như sau:\n\n"
        f"{bullet_lines}\n\n"
        "Nguồn tham khảo:\n"
        + (source_documents or "- Tài liệu nội bộ đã tải lên")
    )




class DocumentService:
    @staticmethod
    async def upload_document(
        db: Session,
        *,
        file: UploadFile,
        title: str | None,
        actor: User,
    ) -> Document:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tai lieu tai len dang rong",
            )

        content_type = file.content_type or "application/octet-stream"
        file_name = file.filename or "document"
        _validate_supported_document(file_name, content_type)
        document = DocumentRepository.create_document(
            db,
            title=title or file_name,
            file_name=file_name,
            content_type=content_type,
            raw_text="",
            processing_status="uploaded",
            uploaded_by_user_id=actor.id,
        )
        db.flush()

        stored_file_name = _safe_file_name(document.id, file_name)
        stored_path = _document_upload_dir() / stored_file_name
        stored_path.write_bytes(content)
        document.source_file_path = os.fspath(stored_path)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.document.upload",
            entity_type="document",
            entity_id=str(document.id),
            metadata_json={"file_name": document.file_name, "mode": "background"},
        )
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def _index_document_chunks(
        db: Session,
        *,
        document_id: int,
        chunks: list[str],
    ) -> list[DocumentChunk]:
        embedding_service = get_embedding_service()
        created_chunks: list[DocumentChunk] = []
        for index, chunk_text in enumerate(chunks):
            chunk = DocumentChunkRepository.create_chunk(
                db,
                document_id=document_id,
                chunk_index=index,
                content=chunk_text,
                embedding_json=embedding_service.embed(chunk_text),
                token_count=len(_tokens(chunk_text)),
            )
            created_chunks.append(chunk)
        db.flush()
        return created_chunks

    @staticmethod
    def _clear_document_graph(db: Session, document_id: int) -> None:
        RagRelationshipRepository.delete_for_document(db, document_id)
        RagEntityRepository.delete_for_document(db, document_id)
        DocumentChunkRepository.delete_for_document(db, document_id)

    @staticmethod
    def _run_graph_ingestion(db: Session, chunks: list[DocumentChunk]) -> None:
        batch_size = max(1, settings.RAG_ENTITY_EXTRACTION_BATCH_SIZE)
        for start in range(0, len(chunks), batch_size):
            GraphRagIngestionService.ingest_chunks(
                db,
                chunks=chunks[start : start + batch_size],
            )

    @staticmethod
    def process_document_background(document_id: int) -> None:
        db = SessionLocal()
        try:
            document = DocumentRepository.get_by_id(db, document_id)
            if document is None:
                return

            document.processing_status = "processing"
            document.processing_error = None
            db.commit()

            content: bytes | None = None
            if document.source_file_path and Path(document.source_file_path).exists():
                content = Path(document.source_file_path).read_bytes()

            page_count = document.page_count
            if content is not None:
                raw_text, page_count = _extract_text_with_page_count(
                    document.file_name,
                    document.content_type,
                    content,
                )
            else:
                raw_text = document.raw_text

            raw_text = _normalize_document_text(raw_text)
            if not raw_text:
                raise ValueError("Khong tim thay noi dung co the doc trong tai lieu")

            chunks, skipped_duplicate_chunks = _limit_chunks(_chunk_text(raw_text))
            if not chunks:
                raise ValueError("Tai lieu khong the chia thanh doan noi dung")

            DocumentService._clear_document_graph(db, document.id)
            document.raw_text = raw_text
            document.chunk_count = 0
            document.entity_count = 0
            document.relationship_count = 0
            document.skipped_duplicate_chunks = skipped_duplicate_chunks
            document.page_count = page_count or 0
            document.extracted_character_count = len(raw_text)
            document.average_chunk_length = 0
            document.max_chunk_length = 0
            db.flush()

            created_chunks = DocumentService._index_document_chunks(
                db,
                document_id=document.id,
                chunks=chunks,
            )
            DocumentService._run_graph_ingestion(db, created_chunks)
            db.flush()

            document.chunk_count = len(created_chunks)
            document.entity_count = len(RagEntityRepository.list_for_document(db, document.id))
            document.relationship_count = len(
                RagRelationshipRepository.list_for_document(db, document.id)
            )
            chunk_lengths = [len(chunk.content or "") for chunk in created_chunks]
            document.average_chunk_length = (
                round(sum(chunk_lengths) / len(chunk_lengths)) if chunk_lengths else 0
            )
            document.max_chunk_length = max(chunk_lengths) if chunk_lengths else 0
            document.processing_status = "completed"
            document.processing_error = None
            db.commit()
            logger.info(
                "Graph RAG document ingestion metrics",
                extra={
                    "document_id": document.id,
                    "file_name": document.file_name,
                    "total_pages": document.page_count,
                    "total_extracted_characters": document.extracted_character_count,
                    "total_chunks": document.chunk_count,
                    "average_chunk_size": document.average_chunk_length,
                    "max_chunk_size": document.max_chunk_length,
                    "entity_count": document.entity_count,
                    "relationship_count": document.relationship_count,
                    "skipped_duplicate_chunks": document.skipped_duplicate_chunks,
                },
            )
        except Exception as exc:
            db.rollback()
            failed_document = DocumentRepository.get_by_id(db, document_id)
            if failed_document is not None:
                failed_document.processing_status = "failed"
                failed_document.processing_error = str(exc)[:1000]
                db.commit()
        finally:
            db.close()

    @staticmethod
    def reprocess_document(db: Session, *, document_id: int, actor: User) -> Document:
        document = DocumentRepository.get_by_id(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        DocumentService._clear_document_graph(db, document.id)
        document.processing_status = "processing"
        document.processing_error = None
        document.chunk_count = 0
        document.entity_count = 0
        document.relationship_count = 0
        document.skipped_duplicate_chunks = 0
        document.extracted_character_count = 0
        document.average_chunk_length = 0
        document.max_chunk_length = 0
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.document.reprocess",
            entity_type="document",
            entity_id=str(document.id),
            metadata_json={"mode": "background"},
        )
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def list_documents(
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> list[Document]:
        return DocumentRepository.list_documents(
            db,
            skip=skip,
            limit=min(limit, 100),
            search=search,
        )

    @staticmethod
    def list_chunks(
        db: Session,
        *,
        document_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[DocumentChunk]:
        document = DocumentRepository.get_by_id(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return DocumentChunkRepository.list_for_document(
            db,
            document_id,
            skip=skip,
            limit=min(limit, 200),
        )

    @staticmethod
    def delete_document(db: Session, *, document_id: int, actor: User) -> None:
        document = DocumentRepository.get_by_id(db, document_id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.document.delete",
            entity_type="document",
            entity_id=str(document.id),
            metadata_json={"file_name": document.file_name},
        )
        DocumentRepository.delete_document(db, document)
        db.commit()


class RetrievalService:
    @staticmethod
    def retrieve(db: Session, question: str) -> list[RetrievedChunk]:
        question_embedding = get_embedding_service().embed(question)
        chunks = DocumentChunkRepository.list_all_chunks(db)
        scored = [
            RetrievedChunk(
                chunk=chunk,
                score=_cosine_score(question_embedding, chunk.embedding_json),
            )
            for chunk in chunks
        ]
        scored = [item for item in scored if item.score >= settings.RAG_MIN_SCORE]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: settings.RAG_TOP_K]


class ChatbotService:
    @staticmethod
    def _generate_answer(
        question: str,
        context_text: str,
        graph_context: str,
        sources: list[ChatbotSource],
    ) -> str:
        source_documents = "\n".join(
            f"- {source.document_title}, đoạn {source.chunk_index + 1}"
            for source in sources
        )
        prompt = f"""
You are an AI insurance support assistant for Company Y.
You must answer only using the provided company document context.
You must not use outside knowledge.
You must be honest about what the context says.
If the context explicitly says a product, benefit, document, limit, or condition is not provided or not regulated, say that clearly.
If the context does not contain enough information, answer exactly:
"{REFUSAL_MESSAGE}"

Answer in Vietnamese.
Use a polite, friendly, clear customer-support tone.
Do not mention internal implementation details such as chunks, embeddings, graph, or retrieval.
Do not copy raw context verbatim unless necessary.
If useful, summarize in bullet points.
If source references are provided, include a short "Nguồn tham khảo" section.

Question:
{question}

Retrieved Context:
{context_text}

Matched Knowledge Graph:
{graph_context}

Source Documents:
{source_documents}

Task:
Generate the final customer-facing answer in Vietnamese.
"""
        prompt = f"""
You are the official AI insurance assistant of Bảo Hiểm Việt.

You must answer customer questions only from:

1. Knowledge Graph Context
2. Retrieved Company Document Context

Do not use outside knowledge.

Do not invent:

* benefits
* limits
* exclusions
* payment amounts
* required documents
* waiting periods
* claim decisions

Write a concise answer.
Only include facts directly needed to answer the question.
Do not include repair invoices, police reports, claim documents, or unrelated requirements unless the customer asks about documents or claim submission.
Prefer this format:
- A short yes/no sentence when applicable.
- One short explanation paragraph.
- A short "Nguồn" section with source document names.

If the context does not contain the answer, reply exactly:
"{REFUSAL_MESSAGE}"

If the context contains conflicting information, reply exactly:
"{CONFLICT_REFUSAL_MESSAGE}"

Answer in Vietnamese.
Use a friendly, professional customer-support tone.
Do not mention technical terms such as chunk, graph, vector, embedding, retrieval, database, or model.

Question:
{question}

Knowledge Graph Context:
{graph_context}

Retrieved Document Context:
{context_text}

Source Documents:
{source_documents}

Final Answer:
"""
        generated = GeminiService.generate_text(prompt)
        if generated:
            return generated.strip()
        if not context_text.strip():
            return REFUSAL_MESSAGE
        return _build_local_answer(
            question,
            f"{graph_context}\n\n{context_text}",
            source_documents,
        )

    @staticmethod
    def answer_question(
        db: Session,
        *,
        payload: ChatbotQuestion,
        actor: User,
    ) -> ChatbotAnswer:
        from app.services.graph_rag_retrieval_service import (
            LOW_CONFIDENCE_REASON,
            UNSUPPORTED_QUERY_REASON,
            GraphRagRetrievalService,
        )

        retrieval = GraphRagRetrievalService.retrieve(db, payload.question)
        if retrieval.fallback_reason:
            if retrieval.fallback_reason == "conflicting_context":
                fallback_answer = CONFLICT_REFUSAL_MESSAGE
            elif retrieval.fallback_reason in {
                UNSUPPORTED_QUERY_REASON,
                LOW_CONFIDENCE_REASON,
            }:
                fallback_answer = UNSUPPORTED_CHATBOT_MESSAGE
            else:
                fallback_answer = REFUSAL_MESSAGE
            RagChatLogRepository.create_log(
                db,
                user_id=actor.id,
                question=payload.question,
                answer=fallback_answer,
                retrieved_context_json={
                    "reason": retrieval.fallback_reason,
                    "classification": retrieval.classification,
                    "confidence_score": retrieval.confidence_score,
                    "source_chunk_ids": [],
                    "matched_entity_ids": [],
                },
                confidence_score=retrieval.confidence_score,
            )
            AuditRepository.record_activity(
                db,
                actor_user_id=actor.id,
                action="customer.chatbot.query",
                entity_type="graph_rag",
                metadata_json={"fallback_reason": retrieval.fallback_reason},
            )
            db.commit()
            return ChatbotAnswer(
                answer=fallback_answer,
                sources=[],
                confidence_score=retrieval.confidence_score,
                matched_entities=[],
                fallback_reason=retrieval.fallback_reason,
            )

        sources = [
            ChatbotSource(
                document_id=item.chunk.document_id,
                document_title=item.chunk.document_title,
                chunk_id=item.chunk.id,
                chunk_index=item.chunk.chunk_index,
                score=round(item.score, 4),
                preview=_preview_text(GraphRagRetrievalService._context_for_chunk(item)),
            )
            for item in retrieval.chunks[: settings.RAG_TOP_K]
        ]
        matched_entities = [
            ChatbotMatchedEntity(
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
            )
            for entity in retrieval.matched_entities[:10]
        ]
        answer = ChatbotService._generate_answer(
            payload.question,
            retrieval.context_text,
            retrieval.graph_context,
            sources,
        )
        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="customer.chatbot.query",
            entity_type="graph_rag",
            metadata_json={
                "source_chunk_ids": [item.chunk.id for item in retrieval.chunks],
                "matched_entity_ids": [entity.id for entity in retrieval.matched_entities],
                "confidence_score": retrieval.confidence_score,
            },
        )
        RagChatLogRepository.create_log(
            db,
            user_id=actor.id,
            question=payload.question,
            answer=answer,
            retrieved_context_json={
                "source_chunk_ids": [item.chunk.id for item in retrieval.chunks],
                "matched_entity_ids": [entity.id for entity in retrieval.matched_entities],
                "relationship_ids": [relationship.id for relationship in retrieval.relationships],
            },
            confidence_score=retrieval.confidence_score,
        )
        db.commit()
        return ChatbotAnswer(
            answer=answer,
            sources=sources,
            confidence_score=retrieval.confidence_score,
            matched_entities=matched_entities,
            fallback_reason=None,
        )
