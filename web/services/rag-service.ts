import { apiFetch } from "@/services/api-client";
import type {
  ChatbotAnswer,
  DocumentChunk,
  DocumentRecord,
} from "@/types/rag";

type DocumentListParams = {
  skip?: number;
  limit?: number;
  search?: string;
};

function toQuery(params: DocumentListParams = {}) {
  const query = new URLSearchParams();
  if (params.skip !== undefined) {
    query.set("skip", String(params.skip));
  }
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.search) {
    query.set("search", params.search);
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export function uploadDocument(token: string, file: File, title?: string) {
  const formData = new FormData();
  formData.set("file", file);
  if (title?.trim()) {
    formData.set("title", title.trim());
  }
  return apiFetch<DocumentRecord>("/admin/documents", {
    method: "POST",
    body: formData,
    token,
  });
}

export function listDocuments(token: string, params?: DocumentListParams) {
  return apiFetch<DocumentRecord[]>(`/admin/documents${toQuery(params)}`, {
    token,
  });
}

export function listDocumentChunks(token: string, documentId: number) {
  return apiFetch<DocumentChunk[]>(`/admin/documents/${documentId}/chunks`, {
    token,
  });
}

export function deleteDocument(token: string, documentId: number) {
  return apiFetch<void>(`/admin/documents/${documentId}`, {
    method: "DELETE",
    token,
  });
}

export function reprocessDocument(token: string, documentId: number) {
  return apiFetch<DocumentRecord>(
    `/admin/documents/${documentId}/reprocess`,
    {
      method: "POST",
      token,
    },
  );
}

export function askChatbot(token: string, question: string) {
  return apiFetch<ChatbotAnswer>("/customer/chatbot/query", {
    method: "POST",
    body: JSON.stringify({ question }),
    token,
  });
}
