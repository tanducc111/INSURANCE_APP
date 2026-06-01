export const roleLabels: Record<string, string> = {
  ADMIN: "Quản trị viên",
  EMPLOYEE: "Nhân viên",
  CUSTOMER: "Khách hàng",
};

export const userStatusLabels: Record<string, string> = {
  active: "Đang hoạt động",
  inactive: "Ngừng hoạt động",
};

export const subscriptionStatusLabels: Record<string, string> = {
  pending: "Chờ kích hoạt",
  active: "Đang hiệu lực",
  expired: "Hết hạn",
  cancelled: "Đã hủy",
};

export const paymentStatusLabels: Record<string, string> = {
  unpaid: "Chưa thanh toán",
  paid: "Đã thanh toán",
  overdue: "Quá hạn",
};

export const claimStatusLabels: Record<string, string> = {
  pending: "Chờ xử lý",
  reviewing: "Đang xem xét",
  need_more_documents: "Cần bổ sung hồ sơ",
  approved: "Đã duyệt",
  rejected: "Từ chối",
  completed: "Hoàn tất",
};

export const appointmentStatusLabels: Record<string, string> = {
  pending: "Chờ xử lý",
  accepted: "Đã chấp nhận",
  rejected: "Từ chối",
  rescheduled: "Đã đổi lịch",
  cancelled: "Đã hủy",
  completed: "Hoàn tất",
};

export const incidentTypeLabels: Record<string, string> = {
  accident: "Tai nạn",
  hospital: "Nằm viện",
  damage: "Thiệt hại tài sản",
  other: "Khác",
};

export const priorityLabels: Record<string, string> = {
  low: "Thấp",
  medium: "Trung bình",
  high: "Cao",
  urgent: "Khẩn cấp",
};

export const tableHeaderLabels: Record<string, string> = {
  actions: "Thao tác",
  assigned: "Ngày phân công",
  customer: "Khách hàng",
  customer_code: "Mã khách hàng",
  employee: "Nhân viên",
  employee_code: "Mã nhân viên",
  email: "Email",
  full_name: "Họ và tên",
  identity_number: "Số CCCD/CMND",
  policy_number: "Số hợp đồng",
  status: "Trạng thái",
};

export const menuLabels: Record<string, string> = {
  appointments: "Lịch hẹn",
  assignments: "Phân công",
  chatbot: "Trợ lý AI",
  chat: "Trò chuyện",
  claims: "Hồ sơ bồi thường",
  customers: "Khách hàng",
  dashboard: "Bảng điều khiển",
  documents: "Tài liệu AI",
  employees: "Nhân viên",
  insurancePackages: "Gói bảo hiểm",
  insuranceProcesses: "Quy trình bảo hiểm",
  subscriptions: "Hợp đồng bảo hiểm",
  users: "Người dùng",
};

export function getRoleLabel(value: string) {
  return roleLabels[value] ?? value;
}

export function getUserStatusLabel(value: string) {
  return userStatusLabels[value] ?? value;
}

export function getSubscriptionStatusLabel(value: string) {
  return subscriptionStatusLabels[value] ?? value;
}

export function getPaymentStatusLabel(value: string) {
  return paymentStatusLabels[value] ?? value;
}

export function getClaimStatusLabel(value: string) {
  return claimStatusLabels[value] ?? value;
}

export function getAppointmentStatusLabel(value: string) {
  return appointmentStatusLabels[value] ?? value;
}

export function getIncidentTypeLabel(value: string) {
  return incidentTypeLabels[value] ?? value;
}

export function getTableHeaderLabel(value: string) {
  return tableHeaderLabels[value] ?? value;
}

export function viLabel(value: string, fallback = value) {
  return (
    claimStatusLabels[value] ??
    appointmentStatusLabels[value] ??
    subscriptionStatusLabels[value] ??
    paymentStatusLabels[value] ??
    userStatusLabels[value] ??
    incidentTypeLabels[value] ??
    priorityLabels[value] ??
    roleLabels[value] ??
    menuLabels[value] ??
    tableHeaderLabels[value] ??
    fallback
  );
}
