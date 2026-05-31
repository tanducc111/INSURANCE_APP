export type AppointmentStatus =
  | "pending"
  | "accepted"
  | "rejected"
  | "rescheduled"
  | "cancelled"
  | "completed";

export type ChatRoom = {
  id: number;
  customer_id: number;
  employee_id: number;
  customer_name: string;
  customer_code: string;
  employee_name: string;
  employee_code: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: number;
  room_id: number;
  sender_user_id: number;
  sender_name: string;
  sender_role: string;
  content: string;
  is_read: boolean;
  created_at: string;
  updated_at: string;
};

export type Appointment = {
  id: number;
  customer_id: number;
  employee_id: number;
  scheduled_at: string;
  duration_minutes: number;
  status: AppointmentStatus;
  note: string | null;
  customer_name: string;
  customer_code: string;
  employee_name: string;
  employee_code: string;
  created_at: string;
  updated_at: string;
};

export type AppointmentPayload = {
  scheduled_at: string;
  duration_minutes: number;
  note?: string | null;
};

export type AppointmentUpdatePayload = Partial<AppointmentPayload> & {
  status?: AppointmentStatus;
};
