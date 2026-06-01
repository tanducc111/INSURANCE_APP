export type DocumentRecord = {
  id: number;
  title: string;
  file_name: string;
  content_type: string;
  chunk_count: number;
  entity_count: number;
  relationship_count: number;
  uploaded_by_user_id: number | null;
  uploaded_by_name: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentChunk = {
  id: number;
  document_id: number;
  document_title: string;
  chunk_index: number;
  content: string;
  token_count: number;
  created_at: string;
  updated_at: string;
};

export type ChatbotSource = {
  document_id: number;
  document_title: string;
  chunk_id: number;
  chunk_index: number;
  score: number;
  preview: string;
};

export type ChatbotAnswer = {
  answer: string;
  sources: ChatbotSource[];
  confidence_score: number;
  matched_entities?: {
    id: number;
    name: string;
    entity_type: string;
    description: string;
  }[];
  fallback_reason?: string | null;
};
