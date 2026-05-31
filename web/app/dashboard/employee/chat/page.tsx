"use client";

import { FormEvent, useEffect, useState } from "react";

import { useRoleAccess } from "@/hooks/use-role-access";
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
      setError(err instanceof ApiError ? err.message : "Unable to load rooms");
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
      setError(err instanceof ApiError ? err.message : "Unable to load messages");
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
      setError(err instanceof ApiError ? err.message : "Unable to send message");
    } finally {
      setIsSending(false);
    }
  }

  if (!isReady) {
    return <p className="text-sm font-medium text-slate-600">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-7xl">
      <header className="border-b border-slate-200 pb-5">
        <p className="text-sm font-medium uppercase text-ocean">Employee</p>
        <h1 className="mt-2 text-3xl font-semibold">Customer Chat</h1>
      </header>

      {error ? (
        <p className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </p>
      ) : null}

      <section className="mt-6 grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="overflow-hidden rounded-md border border-slate-200 bg-white shadow-sm">
          {isLoading ? (
            <p className="p-5 text-sm font-medium text-slate-500">Loading...</p>
          ) : rooms.length === 0 ? (
            <p className="p-5 text-sm font-medium text-slate-500">
              No chat rooms found.
            </p>
          ) : (
            <div className="divide-y divide-slate-200">
              {rooms.map((room) => (
                <button
                  className={`block w-full px-5 py-4 text-left transition ${
                    selectedRoomId === room.id ? "bg-teal-50" : "hover:bg-slate-50"
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

        <section className="rounded-md border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 p-4">
            <h2 className="text-lg font-semibold">
              {selectedRoom ? selectedRoom.customer_name : "Conversation"}
            </h2>
          </div>
          <div className="h-[480px] overflow-y-auto p-5">
            {isMessagesLoading ? (
              <p className="text-sm font-medium text-slate-500">Loading...</p>
            ) : messages.length === 0 ? (
              <p className="text-sm font-medium text-slate-500">
                No messages yet.
              </p>
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
              disabled={!selectedRoomId}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Write a message"
              value={content}
            />
            <button
              className="rounded-md bg-ocean px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={isSending || !selectedRoomId || !content.trim()}
              type="submit"
            >
              {isSending ? "Sending..." : "Send"}
            </button>
          </form>
        </section>
      </section>
    </div>
  );
}
