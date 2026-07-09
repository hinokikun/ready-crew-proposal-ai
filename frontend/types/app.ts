export type UserRole = "admin" | "member" | "viewer";

export type AuthUser = {
  id: number;
  email: string;
  role: UserRole;
  is_active?: boolean;
};

export type LoginResult = {
  authenticated: boolean;
  token: string;
  expires_in_seconds: number;
  message: string;
  user?: AuthUser;
};

export type ManagedUser = {
  id: number;
  email: string;
  role: UserRole;
  is_active: number | boolean;
  created_at: string;
  updated_at: string;
};

export type CrmCustomer = {
  id: number;
  company_name: string;
  industry: string;
  contact_person: string;
  updated_at: string;
};

export type CrmProject = {
  id: number;
  name: string;
  customer_name?: string;
  status: string;
  win_probability: number;
  summary: string;
  next_action: string;
  updated_at: string;
};

export type AuditLog = {
  id: number;
  user_id: number | null;
  user_email?: string | null;
  event_type: string;
  target_type: string;
  target_id: string;
  status: "success" | "failure" | string;
  metadata: string;
  created_at: string;
};

export type FeedbackRating = "usable" | "needs_revision" | "hard_to_use";

export type FeedbackEntry = {
  id: number;
  user_id: number | null;
  user_email?: string | null;
  user_role: UserRole | string;
  rating: FeedbackRating;
  comment: string;
  feature_name: string;
  created_at: string;
};

export type FeedbackSummary = {
  usable: number;
  needs_revision: number;
  hard_to_use: number;
  comments: number;
};
