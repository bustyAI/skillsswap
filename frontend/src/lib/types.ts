export interface Topic {
  id: string;
  name: string;
  description: string | null;
  parent_topic_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TopicListResponse {
  items: Topic[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface TopicBrief {
  id: string;
  name: string;
}

export interface MentorBrief {
  id: string;
  user_id: string;
  headline: string | null;
  rating_avg: number | null;
  rating_count: number;
}

export interface TopicMentorsResponse {
  items: MentorBrief[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface RecommendedMentor {
  id: string;
  user_id: string;
  display_name: string | null;
  avatar_url: string | null;
  headline: string | null;
  bio: string | null;
  rating_avg: number | null;
  rating_count: number;
  score: number;
}

export interface RecommendationsResponse {
  items: RecommendedMentor[];
  topic_id: string;
  cached: boolean;
}

export interface MentorProfile {
  id: string;
  user_id: string;
  bio: string | null;
  headline: string | null;
  is_enabled: boolean;
  rating_avg: number | null;
  rating_count: number;
  last_active_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MentorTopicsResponse {
  topics: TopicBrief[];
}

export interface ReviewerBrief {
  id: string;
  display_name: string | null;
  email: string;
}

export interface Review {
  id: string;
  meeting_id: string;
  reviewer_id: string;
  rating: number;
  comment: string | null;
  editable_until: string;
  created_at: string;
  updated_at: string;
  reviewer: ReviewerBrief | null;
}

export interface ReviewListResponse {
  reviews: Review[];
  total: number;
  page: number;
  page_size: number;
}

export interface MentorshipCreate {
  mentor_id: string;
}

export interface UserBrief {
  id: string;
  display_name: string | null;
  email: string;
}

export interface Mentorship {
  id: string;
  mentor_id: string;
  mentee_id: string;
  status: "REQUESTED" | "ACTIVE" | "DECLINED" | "ENDED";
  created_at: string;
  updated_at: string;
  mentor: UserBrief | null;
  mentee: UserBrief | null;
}

export interface MentorshipListResponse {
  items: Mentorship[];
  total: number;
}

export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface UserUpdateRequest {
  display_name?: string | null;
}

export interface Meeting {
  id: string;
  mentorship_id: string;
  status: "REQUESTED" | "SCHEDULED" | "COMPLETED" | "CANCELLED";
  scheduled_time: string | null;
  meeting_url: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  mentorship?: Mentorship;
}

export interface MeetingListResponse {
  items: Meeting[];
  total: number;
}

export interface MyMentorProfile {
  id: string;
  user_id: string;
  bio: string | null;
  headline: string | null;
  is_enabled: boolean;
  rating_avg: number | null;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

export interface MentorProfileCreateRequest {
  bio?: string | null;
  headline?: string | null;
}

export interface MentorProfileUpdateRequest {
  bio?: string | null;
  headline?: string | null;
}

export interface MentorTopicsUpdateRequest {
  topic_ids: string[];
}

export interface Message {
  id: string;
  thread_id: string;
  sender_id: string;
  body: string;
  created_at: string;
  sender: UserBrief | null;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
  has_next: boolean;
  cursor: string | null;
}

export interface MessageCreate {
  body: string;
}

export interface MeetingScheduleRequest {
  scheduled_time: string;
  meeting_url: string;
}

export interface ReviewCreate {
  rating: number;
  comment?: string | null;
}

export interface ReviewUpdate {
  rating?: number;
  comment?: string | null;
}

export type ReportStatus = "PENDING" | "UNDER_REVIEW" | "RESOLVED" | "DISMISSED";

export interface ReporterBrief {
  id: string;
  email: string;
  display_name: string | null;
}

export interface ReportedUserBrief {
  id: string;
  email: string;
  display_name: string | null;
}

export interface ResolverBrief {
  id: string;
  email: string;
  display_name: string | null;
}

export interface AdminReport {
  id: string;
  reporter_id: string;
  reported_user_id: string | null;
  reported_mentorship_id: string | null;
  reason: string;
  status: ReportStatus;
  resolution_notes: string | null;
  resolved_by_id: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
  reporter: ReporterBrief | null;
  reported_user: ReportedUserBrief | null;
  resolved_by: ResolverBrief | null;
}

export interface AdminReportListResponse {
  reports: AdminReport[];
  total: number;
  page: number;
  page_size: number;
}

export interface ResolveReportRequest {
  resolution_notes: string;
  dismiss?: boolean;
}

export interface AdminUser {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
  banned_at: string | null;
  deleted_at: string | null;
  has_mentor_profile: boolean;
}

export interface AdminUserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}

export interface BanUserRequest {
  reason: string;
}

export interface AdminMentor {
  id: string;
  user_id: string;
  email: string;
  display_name: string | null;
  headline: string | null;
  bio: string | null;
  is_enabled: boolean;
  rating_avg: number | null;
  rating_count: number;
  created_at: string;
}

export interface AdminMentorListResponse {
  mentors: AdminMentor[];
  total: number;
  page: number;
  page_size: number;
}

export interface DisableMentorRequest {
  reason: string;
}

export interface AdminActionResponse {
  success: boolean;
  message: string;
}
