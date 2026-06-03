"use client";

import { FormEvent, useState } from "react";
import { Bot, FileText, SendHorizontal, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { askChatbot } from "@/services/rag-service";
import type { ChatbotSource } from "@/types/rag";

type ChatEntry = {
  id: number;
  question: string;
  answer: string;
  sources: ChatbotSource[];
  confidenceScore: number;
  fallbackReason?: string | null;
};

const suggestedQuestions = [
  "Bảo hiểm xe máy có hỗ trợ tai nạn không?",
  "Tôi cần giấy tờ gì để nộp hồ sơ bồi thường xe máy?",
  "Tôi chưa có hóa đơn sửa chữa thì có nộp hồ sơ được không?",
  "Hồ sơ cần bổ sung chứng từ thì tôi phải làm gì?",
  "Bảo hiểm sức khỏe cao cấp có hỗ trợ phẫu thuật không?",
];

export default function CustomerChatbotPage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitQuestion(nextQuestion: string) {
    if (!token || !nextQuestion.trim()) {
      return;
    }

    const currentQuestion = nextQuestion.trim();
    setQuestion("");
    setIsLoading(true);
    setError(null);
    try {
      const response = await askChatbot(token, currentQuestion);
      setEntries((current) => [
        ...current,
        {
          answer: response.answer,
          id: Date.now(),
          question: currentQuestion,
          sources: response.sources,
          confidenceScore: response.confidence_score,
          fallbackReason: response.fallback_reason,
        },
      ]);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Không thể gửi câu hỏi cho trợ lý AI",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitQuestion(question);
  }

  if (!isReady) {
    return <LoadingState />;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        description="Tôi chỉ trả lời dựa trên tài liệu nội bộ đã được công ty tải lên."
        eyebrow="Khách hàng"
        title="Trợ lý bảo hiểm AI"
      />

      {error ? (
        <p className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 overflow-hidden rounded-lg border border-border bg-white shadow-sm">
        <div className="min-h-[520px] space-y-5 bg-slate-50/70 p-5">
          {entries.length === 0 ? (
            <div className="space-y-5">
              <EmptyState
                description="Chọn một câu hỏi gợi ý hoặc nhập nội dung cần tư vấn về quyền lợi, chứng từ, điều kiện loại trừ hoặc trạng thái hồ sơ bồi thường."
                icon={Bot}
                title="Bạn cần hỗ trợ điều gì?"
              />
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {suggestedQuestions.map((item) => (
                  <button
                    className="rounded-lg border border-border bg-white p-4 text-left text-sm font-semibold leading-6 text-ink shadow-sm transition hover:border-primary hover:text-primary"
                    key={item}
                    onClick={() => void submitQuestion(item)}
                    type="button"
                  >
                    <Sparkles aria-hidden className="mb-3 h-4 w-4 text-primary" />
                    {item}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            entries.map((entry) => (
              <div className="space-y-4" key={entry.id}>
                <div className="flex justify-end">
                  <p className="max-w-[80%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-sm font-medium leading-6 text-white">
                    {entry.question}
                  </p>
                </div>
                <div className="max-w-[88%] rounded-2xl rounded-bl-md border border-border bg-white p-4 shadow-sm">
                  <div className="mb-3 flex items-center gap-2 text-sm font-bold text-primary">
                    <Bot aria-hidden className="h-4 w-4" />
                    Trợ lý bảo hiểm AI
                  </div>
                  <p className="whitespace-pre-line text-sm leading-6 text-slate-700">
                    {entry.answer}
                  </p>
                  {entry.fallbackReason ? (
                    <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
                      Thông tin này chưa đủ căn cứ trong tài liệu nội bộ. Bạn có thể liên hệ nhân viên phụ trách để được hỗ trợ thêm.
                    </p>
                  ) : null}
                  {entry.sources.length > 0 ? (
                    <div className="mt-4 border-t border-border pt-4">
                      <p className="text-xs font-bold uppercase tracking-normal text-muted">
                        Nguồn tham khảo
                      </p>
                      <div className="mt-3 space-y-2">
                        {entry.sources.map((source) => (
                          <div
                            className="rounded-lg border border-border bg-slate-50 p-3"
                            key={`${source.document_id}-${source.chunk_id}`}
                          >
                            <p className="flex items-center gap-2 text-sm font-bold">
                              <FileText aria-hidden className="h-4 w-4 text-primary" />
                              {source.document_title}
                            </p>
                            <p className="mt-1 text-xs text-muted">
                              Đoạn {source.chunk_index + 1} - điểm liên quan {source.score}
                            </p>
                            <p className="mt-2 text-sm leading-6 text-slate-600">
                              {source.preview}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            ))
          )}
          {isLoading ? (
            <div className="inline-flex rounded-full border border-border bg-white px-4 py-2 text-sm font-semibold text-muted shadow-sm">
              Trợ lý đang soạn trả lời...
            </div>
          ) : null}
        </div>

        <form
          className="flex gap-3 border-t border-border bg-white p-4"
          onSubmit={handleSubmit}
        >
          <input
            className="flex-1 rounded-md border border-border px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Nhập câu hỏi từ tài liệu nội bộ công ty"
            value={question}
          />
          <button
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-bold text-white disabled:bg-slate-300"
            disabled={isLoading || !question.trim()}
            type="submit"
          >
            <SendHorizontal aria-hidden className="h-4 w-4" />
            {isLoading ? "Đang hỏi..." : "Gửi"}
          </button>
        </form>
      </section>
    </div>
  );
}
