export type StudyGroup = {
  id: number;
  name: string;
  is_active: boolean;
};

export type VkChat = {
  id: number;
  peer_id: number;
  title: string | null;
  study_group_id: number | null;
  is_active: boolean;
};

export type MemberRole = "unknown" | "student" | "tutor" | "leader";

export type ChatMember = {
  id: string;
  chat_id: number;
  vk_user_id: number;
  first_name: string | null;
  last_name: string | null;
  role: MemberRole;
  is_active: boolean;
};

export type ConfirmationType = "any_message" | "image";

export type Broadcast = {
  id: number;
  title: string;
  message_text: string;
  link: string | null;
  deadline: string;
  confirmation_type: ConfirmationType;
  created_at: string;
  target_count: number;
  recipient_count: number;
};

export type BroadcastResult = {
  id: string;
  target_id: number;
  study_group_name: string;
  vk_user_id: number;
  first_name: string | null;
  last_name: string | null;
  responded: boolean;
  text: string | null;
  attachments: Array<{
    type?: string;
    photo?: { sizes?: Array<{ url?: string }> };
  }>;
  media: Array<{ id: number; content_type: string; size_bytes: number }>;
  responded_at: string | null;
  is_late: boolean | null;
};

export type Student = {
  id: string;
  chat_id: number;
  vk_user_id: number;
  first_name: string;
  last_name: string;
  is_active: boolean;
  first_seen_at: string;
  last_seen_at: string;
  study_group_id: number;
  study_group_name: string;
  chat_title: string | null;
};

export type Statistics = {
  id: string;
  overview: {
    total_groups: number;
    total_students: number;
    active_broadcasts: number;
    completed_broadcasts: number;
    responses_today: number;
  };
  responses_over_time: Array<{ date: string; count: number }>;
  broadcast_completion: Array<{
    id: number;
    title: string;
    deadline: string;
    recipient_count: number;
    response_count: number;
  }>;
  group_activity: Array<{
    id: number;
    name: string;
    student_count: number;
    recipient_count: number;
    response_count: number;
  }>;
};
