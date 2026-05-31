import { apiFetch } from "@/services/api-client";
import type {
  Appointment,
  AppointmentPayload,
  AppointmentStatus,
  AppointmentUpdatePayload,
  ChatMessage,
  ChatRoom,
} from "@/types/communication";

type ListParams = {
  skip?: number;
  limit?: number;
  status?: AppointmentStatus | "all";
};

function toQuery(params: ListParams = {}) {
  const query = new URLSearchParams();
  if (params.skip !== undefined) {
    query.set("skip", String(params.skip));
  }
  if (params.limit !== undefined) {
    query.set("limit", String(params.limit));
  }
  if (params.status && params.status !== "all") {
    query.set("status", params.status);
  }
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

export function getCustomerChatRoom(token: string) {
  return apiFetch<ChatRoom>("/customer/chat-room", { token });
}

export function listEmployeeChatRooms(token: string, params?: ListParams) {
  return apiFetch<ChatRoom[]>(`/employee/chat-rooms${toQuery(params)}`, {
    token,
  });
}

export function listChatMessages(
  token: string,
  roomId: number,
  params?: ListParams,
) {
  return apiFetch<ChatMessage[]>(
    `/chat/rooms/${roomId}/messages${toQuery(params)}`,
    { token },
  );
}

export function sendChatMessage(token: string, roomId: number, content: string) {
  return apiFetch<ChatMessage>(`/chat/rooms/${roomId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
    token,
  });
}

export function markChatMessagesRead(token: string, roomId: number) {
  return apiFetch<{ updated: number }>(`/chat/rooms/${roomId}/read`, {
    method: "PATCH",
    token,
  });
}

export function createCustomerAppointment(
  token: string,
  payload: AppointmentPayload,
) {
  return apiFetch<Appointment>("/customer/appointments", {
    method: "POST",
    body: JSON.stringify(payload),
    token,
  });
}

export function listCustomerAppointments(token: string, params?: ListParams) {
  return apiFetch<Appointment[]>(`/customer/appointments${toQuery(params)}`, {
    token,
  });
}

export function listEmployeeAppointments(token: string, params?: ListParams) {
  return apiFetch<Appointment[]>(`/employee/appointments${toQuery(params)}`, {
    token,
  });
}

export function updateEmployeeAppointment(
  token: string,
  appointmentId: number,
  payload: AppointmentUpdatePayload,
) {
  return apiFetch<Appointment>(`/employee/appointments/${appointmentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export function listAdminAppointments(token: string, params?: ListParams) {
  return apiFetch<Appointment[]>(`/admin/appointments${toQuery(params)}`, {
    token,
  });
}
