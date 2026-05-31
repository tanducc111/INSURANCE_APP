"use client";

import { FormEvent, useEffect, useState } from "react";

import { useRoleAccess } from "@/hooks/use-role-access";
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
      setError(err instanceof ApiError ? err.message : "Unable to load messages");
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
        setError(err instanceof ApiError ? err.message : "Unable to load chat");
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
      setError(err instanceof ApiError ? err.message : "Unable to send message");
    } finally {
      setIsSending(false);
    }
  }

  if (!isReady || isLoading) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-5xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Customer</p>
        <h1 className="mt-2 text-3xl font-semibold">Chat</h1>
        {room ? (
          <p className="mt-2 text-sm font-medium text-slate-500">
            Assigned employee: {room.employee_name}
          </p>
        ) : null}
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 rounded-md border border-slate-200 bg-white shadow-sm">
        <div className="h-[520px] overflow-y-auto p-5">
          {messages.length === 0 ? (
            <p className="text-sm font-medium text-slate-500">
              No messages yet.
            </p>
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
                      className={`max-w-[75%] rounded-md px-4 py-3 text-sm ${
                        isMine
                          ? "bg-ocean text-white"
                          : "border border-slate-200 bg-slate-50 text-slate-700"
                      }`}
                    >
                      <p>{message.content}</p>
                      <p className="mt-2 text-xs opacity-75">
                        {message.sender_name} -{" "}
                        {new Date(message.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <form
          className="flex gap-3 border-t border-slate-200 p-4"
          onSubmit={handleSubmit}
        >
          <input
            className="flex-1 rounded-md border border-slate-300 px-3 py-2"
            onChange={(event) => setContent(event.target.value)}
            placeholder="Write a message"
            value={content}
          />
          <button
            className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
            disabled={isSending || !content.trim()}
            type="submit"
          >
            {isSending ? "Sending..." : "Send"}
          </button>
        </form>
      </section>
    </div>
  );
}
