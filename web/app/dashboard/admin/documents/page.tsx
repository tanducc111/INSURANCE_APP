"use client";

import { FormEvent, useEffect, useState } from "react";
import { AlertTriangle, FileText, RefreshCw, Trash2, UploadCloud } from "lucide-react";

import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  deleteDocument,
  listDocumentChunks,
  listDocuments,
  reprocessDocument,
  uploadDocument,
} from "@/services/rag-service";
import type { DocumentChunk, DocumentRecord } from "@/types/rag";

const DOCUMENT_STATUS_LABELS: Record<string, string> = {
  uploaded: "Đã tải lên",
  processing: "Đang xử lý",
  completed: "Hoàn tất",
  failed: "Thất bại",
};

function getDocumentStatusLabel(status: string) {
  return DOCUMENT_STATUS_LABELS[status] ?? status;
}

export default function AdminDocumentsPage() {
  const { isReady, token } = useAdminAccess();
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [isChunksLoading, setIsChunksLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedDocument =
    documents.find((document) => document.id === selectedDocumentId) ?? null;

  async function loadDocuments() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listDocuments(token, { search, limit: 100 });
      setDocuments(data);
      setSelectedDocumentId((current) =>
        data.some((document) => document.id === current)
          ? current
          : data[0]?.id ?? null,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải tài liệu");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadChunks(documentId: number) {
    if (!token) {
      return;
    }

    setIsChunksLoading(true);
    setError(null);
    try {
      setChunks(await listDocumentChunks(token, documentId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải đoạn tài liệu");
    } finally {
      setIsChunksLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadDocuments();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedDocumentId) {
      void loadChunks(selectedDocumentId);
    } else {
      setChunks([]);
    }
  }, [selectedDocumentId, token]);

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadDocuments();
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !file) {
      return;
    }

    setIsUploading(true);
    setError(null);
    try {
      const uploaded = await uploadDocument(token, file, title);
      setTitle("");
      setFile(null);
      await loadDocuments();
      setSelectedDocumentId(uploaded.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải tài liệu lên");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleReprocess(documentId: number) {
    if (!token) {
      return;
    }

    setIsReprocessing(true);
    setError(null);
    try {
      const updated = await reprocessDocument(token, documentId);
      setDocuments((current) =>
        current.map((document) =>
          document.id === updated.id ? updated : document,
        ),
      );
      setSelectedDocumentId(updated.id);
      await loadChunks(updated.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể xử lý lại tài liệu");
    } finally {
      setIsReprocessing(false);
    }
  }

  async function handleDelete(documentId: number) {
    if (!token) {
      return;
    }

    setError(null);
    try {
      await deleteDocument(token, documentId);
      if (selectedDocumentId === documentId) {
        setSelectedDocumentId(null);
      }
      await loadDocuments();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể xóa tài liệu");
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Đang tải...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Quản trị</p>
        <h1 className="mt-2 text-3xl font-semibold">Tài liệu AI</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 xl:grid-cols-[380px_1fr]">
        <form
          className="rounded-md border border-slate-200 bg-white p-5 shadow-sm"
          onSubmit={handleUpload}
        >
          <h2 className="text-lg font-semibold">Tải tài liệu lên</h2>
          <p className="mt-2 text-sm text-slate-500">
            Hỗ trợ PDF, TXT hoặc Markdown. Sau khi tải lên, hệ thống sẽ trích xuất đoạn nội dung, thực thể và quan hệ nghiệp vụ.
          </p>
          <div className="mt-5 grid gap-4">
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Tiêu đề"
              value={title}
            />
            <input
              accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
              className="rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
              type="file"
            />
            <button
              className="inline-flex items-center justify-center gap-2 rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={isUploading || !file}
              type="submit"
            >
              <UploadCloud className="h-4 w-4" aria-hidden="true" />
              {isUploading ? "Đang tải lên..." : "Tải lên"}
            </button>
          </div>
        </form>

        <section>
          <form className="flex flex-wrap gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm kiếm tài liệu"
              value={search}
            />
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >
              Tìm kiếm
            </button>
            <button
              className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              onClick={() => void loadDocuments()}
              type="button"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Làm mới trạng thái
            </button>
          </form>

          <div className="mt-5 overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
            {isLoading ? (
              <p className="p-5 text-sm font-medium text-slate-500">Đang tải...</p>
            ) : documents.length === 0 ? (
              <p className="p-5 text-sm font-medium text-slate-500">
                Chưa có tài liệu.
              </p>
            ) : (
              <div className="divide-y divide-slate-200">
                {documents.map((document) => (
                  <div
                    className={`grid gap-3 px-5 py-4 ${
                      selectedDocumentId === document.id ? "bg-teal-50" : ""
                    }`}
                    key={document.id}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <button
                        className="min-w-0 text-left"
                        onClick={() => setSelectedDocumentId(document.id)}
                        type="button"
                      >
                        <p className="font-semibold">{document.title}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {document.file_name}
                        </p>
                      </button>
                      <div className="flex gap-2">
                        <button
                          className="inline-flex items-center gap-1 rounded-md border border-blue-200 px-3 py-1 text-xs font-semibold text-blue-700 disabled:opacity-60"
                          disabled={isReprocessing || document.processing_status === "processing"}
                          onClick={() => void handleReprocess(document.id)}
                          type="button"
                        >
                          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
                          Xử lý lại
                        </button>
                        <button
                          className="inline-flex items-center gap-1 rounded-md border border-red-200 px-3 py-1 text-xs font-semibold text-red-700"
                          onClick={() => void handleDelete(document.id)}
                          type="button"
                        >
                          <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                          Xóa
                        </button>
                      </div>
                    </div>

                    <div className="grid gap-2 text-xs text-slate-600 sm:grid-cols-3 lg:grid-cols-6">
                      <span>Số trang: {document.page_count}</span>
                      <span>Số đoạn nội dung: {document.chunk_count}</span>
                      <span>Số ký tự: {document.extracted_character_count}</span>
                      <span>Độ dài TB: {document.average_chunk_length}</span>
                      <span>Đoạn lớn nhất: {document.max_chunk_length}</span>
                      <span>Số thực thể: {document.entity_count}</span>
                      <span>Số quan hệ: {document.relationship_count}</span>
                      <span>Đoạn trùng lặp bỏ qua: {document.skipped_duplicate_chunks}</span>
                      <span>Trạng thái: {getDocumentStatusLabel(document.processing_status)}</span>
                      <span>
                        Cảnh báo: {document.conflict_warning ? "Có" : "Không"}
                      </span>
                    </div>

                    {document.conflict_warning ? (
                      <p className="inline-flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800">
                        <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                        {document.conflict_warning}
                      </p>
                    ) : null}

                    {document.processing_status === "processing" ? (
                      <p className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-blue-800">
                        Tài liệu đang được xử lý. Bạn có thể tiếp tục sử dụng hệ thống và quay lại sau.
                      </p>
                    ) : null}

                    {document.processing_status === "failed" ? (
                      <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">
                        Xử lý tài liệu thất bại
                        {document.processing_error ? `: ${document.processing_error}` : "."}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="mt-6 rounded-md border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">
              {selectedDocument ? selectedDocument.title : "Đoạn tài liệu"}
            </h2>
            {isChunksLoading ? (
              <p className="mt-5 text-sm font-medium text-slate-500">Đang tải...</p>
            ) : chunks.length === 0 ? (
              <p className="mt-5 text-sm font-medium text-slate-500">
                Chưa có đoạn tài liệu để xem trước.
              </p>
            ) : (
              <div className="mt-5 space-y-3">
                {chunks.slice(0, 5).map((chunk) => (
                  <div
                    className="rounded-md border border-slate-200 p-4"
                    key={chunk.id}
                  >
                    <p className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
                      <FileText className="h-3.5 w-3.5" aria-hidden="true" />
                      Đoạn {chunk.chunk_index + 1} - {chunk.token_count} từ khóa
                    </p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </section>
    </div>
  );
}
