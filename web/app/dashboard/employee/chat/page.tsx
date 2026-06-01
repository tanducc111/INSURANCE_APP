"use client";

import { FormEvent, useEffect, useState } from "react";

import { EmptyState } from "@/components/ui/empty-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { useRoleAccess } from "@/hooks/use-role-access";
import { formatDateTime } from "@/lib/formatters";
import { ApiError } from "@/services/api-client";
import {
  listChatMessages,
  listEmployeeChatRooms,
  markChatMessagesRead,
  sendChatMessage,
} from "@/services/communication-service";
import type { ChatMessage, ChatRoom } from "@/types/communication";

export default function EmployeeChatPage() {
  const { isReady, token } = useRoleAccess(["EMPLOYEE"]);
  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [selectedRoomId, setSelectedRoomId] = useState<number | null>(null);
  const [content, setContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isMessagesLoading, setIsMessagesLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRoom = rooms.find((room) => room.id === selectedRoomId) ?? null;

  async function loadRooms() {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await listEmployeeChatRooms(token, { limit: 100 });
      setRooms(data);
      setSelectedRoomId((current) => current || data[0]?.id || null);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Không thể tải cuộc trò chuyện",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function loadMessages(roomId: number) {
    if (!token) {
      return;
    }

    setIsMessagesLoading(true);
    setError(null);
    try {
      const data = await listChatMessages(token, roomId, { limit: 100 });
      setMessages(data);
      await markChatMessagesRead(token, roomId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải tin nhắn");
    } finally {
      setIsMessagesLoading(false);
    }
  }

  useEffect(() => {
    if (isReady) {
      void loadRooms();
    }
  }, [isReady, token]);

  useEffect(() => {
    if (selectedRoomId) {
      void loadMessages(selectedRoomId);
    } else {
      setMessages([]);
    }
  }, [selectedRoomId, token]);

  useEffect(() => {
    if (!token || !selectedRoomId) {
      return;
    }
    const interval = window.setInterval(() => {
      void loadMessages(selectedRoomId);
    }, 10000);
    return () => window.clearInterval(interval);
  }, [selectedRoomId, token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedRoomId || !content.trim()) {
      return;
    }

    setIsSending(true);
    setError(null);
    try {
      await sendChatMessage(token, selectedRoomId, content.trim());
      setContent("");
      await loadMessages(selectedRoomId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể gửi tin nhắn");
    } finally {
      setIsSending(false);
    }
  }

  if (!isReady) {
    return <LoadingState />;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        description="Theo dõi hội thoại, phản hồi câu hỏi và hỗ trợ khách hàng được phân công."
        eyebrow="Nhân viên"
        title="Tin nhắn khách hàng"
      />

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="overflow-hidden rounded-lg border border-border bg-white shadow-sm">
          {isLoading ? (
            <LoadingState />
          ) : rooms.length === 0 ? (
            <EmptyState title="Chưa có cuộc trò chuyện" />
          ) : (
            <div className="divide-y divide-slate-200">
              {rooms.map((room) => (
                <button
                  className={`block w-full px-5 py-4 text-left transition ${
                    selectedRoomId === room.id ? "bg-blue-50" : "hover:bg-slate-50"
                  }`}
                  key={room.id}
                  onClick={() => setSelectedRoomId(room.id)}
                  type="button"
                >
                  <p className="font-semibold">{room.customer_name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {room.customer_code}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        <section className="overflow-hidden rounded-lg border border-border bg-white shadow-sm">
          <div className="border-b border-border p-4">
            <h2 className="text-lg font-semibold">
              {selectedRoom ? selectedRoom.customer_name : "Cuộc trò chuyện"}
            </h2>
          </div>
          <div className="h-[520px] overflow-y-auto bg-slate-50/70 p-5">
            {isMessagesLoading ? (
              <LoadingState />
            ) : messages.length === 0 ? (
              <EmptyState title="Chưa có tin nhắn" />
            ) : (
              <div className="space-y-3">
                {messages.map((message) => {
                  const isMine = message.sender_role === "EMPLOYEE";
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
              disabled={!selectedRoomId}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Nhập tin nhắn"
              value={content}
            />
            <button
              className="rounded-md bg-primary px-4 py-2 text-sm font-bold text-white disabled:bg-slate-300"
              disabled={isSending || !selectedRoomId || !content.trim()}
              type="submit"
            >
              {isSending ? "Đang gửi..." : "Gửi"}
            </button>
          </form>
        </section>
      </section>
    </div>
  );
}
