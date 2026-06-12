import axios from 'axios';
import { api } from './client';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ReceptionistConfig {
  id: string;
  sub_account_id: string;
  prompt_context: string;
  model_provider: 'anthropic' | 'openai' | 'ollama';
  web_chat_enabled: boolean;
  sms_enabled: boolean;
  updated_at: string;
}

export interface ChatSession {
  id: string;
  visitor_key: string;
  transcript: { role: 'user' | 'assistant'; content: string; at: string }[];
  extracted: { name?: string; phone?: string };
  contact_id: string | null;
  created_at: string;
  updated_at: string;
}

export const receptionistApi = {
  getConfig: () => api.get<ReceptionistConfig>('/receptionist/config'),
  updateConfig: (data: Partial<ReceptionistConfig>) =>
    api.patch<ReceptionistConfig>('/receptionist/config', data),
  train: (source: string, append = false) =>
    api.post<ReceptionistConfig>('/receptionist/config/train', { source, append }),
  sessions: () => api.get<ChatSession[]>('/receptionist/sessions'),
  promote: (sessionId: string) =>
    api.post(`/receptionist/sessions/${sessionId}/promote`),
  // Public widget endpoint (the same one external sites call)
  chat: (subAccountId: string, visitorKey: string, message: string) =>
    axios.post<{ reply: string; session_id: string; contact_created: boolean }>(
      `${API_BASE}/api/v1/public/chat/${subAccountId}`,
      { visitor_key: visitorKey, message }
    ),
};
