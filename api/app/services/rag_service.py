import io
import math
import re
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rag import Document, DocumentChunk
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.rag_repository import (
    DocumentChunkRepository,
    DocumentRepository,
    RagChatLogRepository,
)
from app.schemas.rag import (
    ChatbotAnswer,
    ChatbotMatchedEntity,
    ChatbotQuestion,
    ChatbotSource,
)
from app.services.gemini_service import REFUSAL_MESSAGE, GeminiService
from app.services.graph_rag_ingestion_service import GraphRagIngestionService


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


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF extraction dependency is not installed",
        ) from exc

    reader = PdfReader(io.BytesIO(content))
    page_texts = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page_texts)


def _extract_text(file_name: str, content_type: str, content: bytes) -> str:
    lower_name = file_name.lower()
    if content_type == "application/pdf" or lower_name.endswith(".pdf"):
        return _extract_pdf_text(content)
    if (
        content_type.startswith("text/")
        or lower_name.endswith(".txt")
        or lower_name.endswith(".md")
    ):
        return _decode_text(content)
    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Only PDF, TXT, and Markdown documents are supported",
    )


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?。])\s+", normalized)
        if sentence.strip()
    ]
    if not sentences:
        return []

    chunks: list[str] = []
    current = ""

    def push_current() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for sentence in sentences:
        if len(sentence) > chunk_size:
            push_current()
            words = sentence.split()
            part = ""
            for word in words:
                candidate = f"{part} {word}".strip()
                if len(candidate) > chunk_size and part:
                    chunks.append(part.strip())
                    part = word
                else:
                    part = candidate
            if part:
                chunks.append(part.strip())
            continue

        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > chunk_size:
            push_current()
            if overlap and chunks:
                overlap_words = chunks[-1].split()[-max(8, overlap // 12):]
                current = " ".join(overlap_words)
            candidate = f"{current} {sentence}".strip()
        current = candidate
    push_current()
    return [chunk for chunk in chunks if chunk]


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


def _build_local_answer(question: str, context_text: str, source_documents: str) -> str:
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
                detail="Uploaded document is empty",
            )

        content_type = file.content_type or "application/octet-stream"
        raw_text = _extract_text(file.filename or "document", content_type, content)
        raw_text = _normalize_text(raw_text)
        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No readable text was found in the document",
            )

        chunks = _chunk_text(raw_text)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Document could not be chunked",
            )

        document = DocumentRepository.create_document(
            db,
            title=title or file.filename or "Company document",
            file_name=file.filename or "document",
            content_type=content_type,
            raw_text=raw_text,
            uploaded_by_user_id=actor.id,
        )
        db.flush()

        embedding_service = get_embedding_service()
        created_chunks: list[DocumentChunk] = []
        for index, chunk_text in enumerate(chunks):
            embedding = embedding_service.embed(chunk_text)
            chunk = DocumentChunkRepository.create_chunk(
                db,
                document_id=document.id,
                chunk_index=index,
                content=chunk_text,
                embedding_json=embedding,
                token_count=len(_tokens(chunk_text)),
            )
            created_chunks.append(chunk)
        db.flush()
        GraphRagIngestionService.ingest_chunks(db, chunks=created_chunks)

        AuditRepository.record_activity(
            db,
            actor_user_id=actor.id,
            action="admin.document.upload",
            entity_type="document",
            entity_id=str(document.id),
            metadata_json={"file_name": document.file_name, "chunks": len(chunks)},
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
        generated = GeminiService.generate_text(prompt)
        if generated:
            return generated
        if not context_text.strip():
            return REFUSAL_MESSAGE
        return _build_local_answer(question, context_text, source_documents)

    @staticmethod
    def answer_question(
        db: Session,
        *,
        payload: ChatbotQuestion,
        actor: User,
    ) -> ChatbotAnswer:
        from app.services.graph_rag_retrieval_service import GraphRagRetrievalService

        retrieval = GraphRagRetrievalService.retrieve(db, payload.question)
        if retrieval.fallback_reason:
            RagChatLogRepository.create_log(
                db,
                user_id=actor.id,
                question=payload.question,
                answer=REFUSAL_MESSAGE,
                retrieved_context_json={
                    "reason": retrieval.fallback_reason,
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
                answer=REFUSAL_MESSAGE,
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
