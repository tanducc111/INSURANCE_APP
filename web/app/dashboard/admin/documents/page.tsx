"use client";

import { FormEvent, useEffect, useState } from "react";

import { useAdminAccess } from "@/hooks/use-admin-access";
import { ApiError } from "@/services/api-client";
import {
  deleteDocument,
  listDocumentChunks,
  listDocuments,
  uploadDocument,
} from "@/services/rag-service";
import type { DocumentChunk, DocumentRecord } from "@/types/rag";

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
      setError(err instanceof ApiError ? err.message : "Không thể tải tài liệu");
    } finally {
      setIsUploading(false);
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
              className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={isUploading || !file}
              type="submit"
            >
              {isUploading ? "Đang tải lên..." : "Tải lên"}
            </button>
          </div>
        </form>

        <section>
          <form className="flex gap-3" onSubmit={handleSearch}>
            <input
              className="min-w-64 flex-1 rounded-md border border-slate-300 px-3 py-2"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Tìm kiếm tài liệu"
              value={search}
            />
            <button
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold"
              type="submit"
            >Tìm kiếm</button>
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
                    className={`flex flex-wrap items-center justify-between gap-3 px-5 py-4 ${
                      selectedDocumentId === document.id ? "bg-teal-50" : ""
                    }`}
                    key={document.id}
                  >
                    <button
                      className="text-left"
                      onClick={() => setSelectedDocumentId(document.id)}
                      type="button"
                    >
                      <p className="font-semibold">{document.title}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {document.file_name} - {document.chunk_count} chunks
                      </p>
                    </button>
                    <button
                      className="rounded-md border border-red-200 px-3 py-1 text-xs font-semibold text-red-700"
                      onClick={() => void handleDelete(document.id)}
                      type="button"
                    >
                      Xóa
                    </button>
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
                No chunks to preview.
              </p>
            ) : (
              <div className="mt-5 space-y-3">
                {chunks.slice(0, 5).map((chunk) => (
                  <div
                    className="rounded-md border border-slate-200 p-4"
                    key={chunk.id}
                  >
                    <p className="text-xs font-semibold uppercase text-slate-500">
                      Chunk {chunk.chunk_index + 1} - {chunk.token_count} tokens
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
