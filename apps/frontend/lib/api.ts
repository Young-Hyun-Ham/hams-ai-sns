import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE
});

export type Bot = {
  id: number;
  user_id: number;
  name: string;
  persona: string;
  topic: string;
  ai_provider: 'mock' | 'gpt' | 'gemini' | 'claude';
  ai_model: string;
  has_api_key: boolean;
  is_active: boolean;
};

export type AIModelListResponse = {
  models: string[];
};

export type SnsPost = {
  id: number;
  user_id: number;
  bot_id: number | null;
  bot_name: string | null;
  category: "경제" | "문화" | "연예" | "유머";
  title: string;
  content: string;
  is_anonymous: boolean;
  created_at: string;
  updated_at: string;
  comment_count: number;
  can_edit: boolean;
};

export const authHeader = (token: string) => ({ Authorization: `Bearer ${token}` });


export type SnsComment = {
  id: number;
  post_id: number;
  user_id: number;
  bot_id: number | null;
  bot_name: string | null;
  content: string;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
};
