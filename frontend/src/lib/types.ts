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
