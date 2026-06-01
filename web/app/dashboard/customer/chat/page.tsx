"use client";

import { FormEvent, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { useRoleAccess } from "@/hooks/use-role-access";
import { formatDateTime } from "@/lib/formatters";
import { ApiError } from "@/services/api-client";
import {
  getCustomerChatRoom,
  listChatMessages,
  markChatMessagesRead,
  sendChatMessage,
} from "@/services/communication-service";
import type { ChatMessage, ChatRoom } from "@/types/communication";

export default function CustomerChatPage() {
  const { isReady, token } = useRoleAccess(["CUSTOMER"]);
  const [room, setRoom] = useState<ChatRoom | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadMessages(roomId: number) {
    if (!token) {
      return;
    }
    try {
      const data = await listChatMessages(token, roomId, { limit: 100 });
      setMessages(data);
      await markChatMessagesRead(token, roomId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải tin nhắn");
    }
  }

  useEffect(() => {
    async function loadRoom() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const roomData = await getCustomerChatRoom(token);
        setRoom(roomData);
        await loadMessages(roomData.id);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Không thể tải cuộc trò chuyện",
        );
      } finally {
        setIsLoading(false);
      }
    }

    if (isReady) {
      void loadRoom();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (!token || !room) {
      return;
    }
    const interval = window.setInterval(() => {
      void loadMessages(room.id);
    }, 10000);
    return () => window.clearInterval(interval);
  }, [room?.id, token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !room || !content.trim()) {
      return;
    }

    setIsSending(true);
    setError(null);
    try {
      await sendChatMessage(token, room.id, content.trim());
      setContent("");
      await loadMessages(room.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể gửi tin nhắn");
    } finally {
      setIsSending(false);
    }
  }

  if (!isReady || isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        description={
          room
            ? `Nhân viên phụ trách: ${room.employee_name}`
            : "Trao đổi trực tiếp với nhân viên phụ trách."
        }
        eyebrow="Khách hàng"
        title="Chat hỗ trợ"
      />

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 overflow-hidden rounded-lg border border-border bg-white shadow-sm">
        <div className="h-[560px] overflow-y-auto bg-slate-50/70 p-5">
          {messages.length === 0 ? (
            <EmptyState title="Chưa có tin nhắn" />
          ) : (
            <div className="space-y-3">
              {messages.map((message) => {
                const isMine = message.sender_role === "CUSTOMER";
                return (
                  <div
                    className={`flex ${isMine ? "justify-end" : "justify-start"}`}
                    key={message.id}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                        isMine
                          ? "rounded-br-md bg-primary text-white"
                          : "rounded-bl-md border border-border bg-white text-slate-700"
                      }`}
                    >
                      <p>{message.content}</p>
                      <p className="mt-2 text-xs opacity-75">
                        {message.sender_name} - {formatDateTime(message.created_at)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <form
          className="flex gap-3 border-t border-border p-4"
          onSubmit={handleSubmit}
        >
          <input
            className="flex-1 rounded-md border border-border px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
            onChange={(event) => setContent(event.target.value)}
            placeholder="Nhập tin nhắn"
            value={content}
          />
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-bold text-white disabled:bg-slate-300"
            disabled={isSending || !content.trim()}
            type="submit"
          >
            {isSending ? "Đang gửi..." : "Gửi"}
          </button>
        </form>
      </section>
    </div>
  );
}
