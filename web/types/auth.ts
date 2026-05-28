export type UserRole = "ADMIN" | "EMPLOYEE" | "CUSTOMER";

export type UserStatus = "active" | "inactive";

export type AuthUser = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  updated_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};
