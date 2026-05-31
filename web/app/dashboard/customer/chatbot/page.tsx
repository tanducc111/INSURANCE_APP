"use client";

import { FormEvent, useState } from "react";

import { useRoleAccess } from "@/hooks/use-role-access";
import { ApiError } from "@/services/api-client";
import { askChatbot } from "@/services/rag-service";
import type { ChatbotSource } from "@/types/rag";

type ChatEntry = {
  id: number;
  question: string;
  answer: string;
  sources: ChatbotSource[];
};

export default function CustomerChatbotPage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [question, setQuestion] = useState("");
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !question.trim()) {
      return;
    }

    const currentQuestion = question.trim();
    setQuestion("");
    setIsLoading(true);
    setError(null);
    try {
      const response = await askChatbot(token, currentQuestion);
      setEntries((current) => [
        ...current,
        {
          id: Date.now(),
          question: currentQuestion,
          answer: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to ask chatbot");
    } finally {
      setIsLoading(false);
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <h1 className="mt-2 text-3xl font-semibold">Company Chatbot</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="min-h-[500px] space-y-5 p-5">
          {entries.length === 0 ? (
            <p className="text-sm font-medium text-slate-500">
              Ask a question about uploaded company documents.
            </p>
          ) : (
            entries.map((entry) => (
              <div className="space-y-3" key={entry.id}>
                <div className="flex justify-end">
                  <p className="max-w-[80%] rounded-md bg-ocean px-4 py-3 text-sm text-white">
                    {entry.question}
                  </p>
                </div>
                <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                  <p className="whitespace-pre-line text-sm leading-6 text-slate-700">
                    {entry.answer}
                  </p>
                  {entry.sources.length > 0 ? (
                    <div className="mt-4 border-t border-slate-200 pt-4">
                      <p className="text-xs font-semibold uppercase text-slate-500">
                        Sources
                      </p>
                      <div className="mt-3 space-y-2">
                        {entry.sources.map((source) => (
                          <div
                            className="rounded-md border border-slate-200 bg-white p-3"
                            key={`${source.document_id}-${source.chunk_id}`}
                          >
                            <p className="text-sm font-semibold">
                              {source.document_title}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              Chunk {source.chunk_index + 1} - score{" "}
                              {source.score}
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
            <p className="text-sm font-medium text-slate-500">Thinking...</p>
          ) : null}
        </div>

        <form
          className="flex gap-3 border-t border-slate-200 p-4"
          onSubmit={handleSubmit}
        >
          <input
            className="flex-1 rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask from company documents"
            value={question}
          />
          <button
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={isLoading || !question.trim()}
            type="submit"
          >
            {isLoading ? "Asking..." : "Ask"}
          </button>
        </form>
      </section>
    </div>
  );
}
