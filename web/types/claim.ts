export type ClaimIncidentType = "accident" | "hospital" | "damage" | "other";

export type ClaimStatus =
  | "pending"
  | "reviewing"
  | "need_more_documents"
  | "approved"
  | "rejected"
  | "completed";

export type ClaimPriority = "low" | "medium" | "high" | "urgent";

export type ClaimAttachmentPayload = {
  file_name: string;
  file_url: string;
  mime_type?: string | null;
  file_size?: number | null;
};

export type ClaimAttachment = ClaimAttachmentPayload & {
  id: number;
  claim_id: number;
  created_at: string;
  updated_at: string;
};

export type ClaimPayload = {
  subscription_id: number;
  title: string;
  description: string;
  incident_type: ClaimIncidentType;
  incident_date: string;
  location?: string | null;
  priority: ClaimPriority;
  attachments?: ClaimAttachmentPayload[];
};

export type Claim = {
  id: number;
  customer_id: number;
  subscription_id: number;
  assigned_employee_id: number | null;
  title: string;
  description: string;
  incident_type: ClaimIncidentType;
  incident_date: string;
  location: string | null;
  status: ClaimStatus;
  priority: ClaimPriority;
  review_note: string | null;
  customer_name: string;
  customer_code: string;
  policy_number: string;
  package_name: string;
  assigned_employee_name: string | null;
  assigned_employee_code: string | null;
  attachments: ClaimAttachment[];
  created_at: string;
  updated_at: string;
};
