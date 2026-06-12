import axios from 'axios';
import { getActiveSubAccountId, SubAccount } from '../store/subAccountStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_PREFIX = '/api/v1';

export const api = axios.create({
  baseURL: `${API_BASE}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Every request is stamped with the active workspace. The backend rejects
// tenant-scoped routes without this header — strict workspace isolation.
api.interceptors.request.use((config) => {
  const subAccountId = getActiveSubAccountId();
  if (subAccountId) {
    config.headers['X-SubAccount-ID'] = subAccountId;
  }
  return config;
});

export function wsUrl(path: string): string {
  const base = API_BASE.replace(/^http/, 'ws');
  return `${base}${path}`;
}

// ============ Types ============

export interface Contact {
  id: string;
  sub_account_id: string;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  status: string;
  do_not_disturb: boolean;
  sms_consent: boolean;
  email_consent: boolean;
  source: string | null;
  tags: string[];
  custom_fields: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Note {
  id: string;
  contact_id: string;
  body: string;
  author: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  contact_id: string;
  channel: string;
  status: 'open' | 'closed' | 'snoozed';
  ai_enabled: boolean;
  unread_count: number;
  last_message_preview: string | null;
  last_message_at: string | null;
  created_at: string;
}

export interface Message {
  id: string;
  contact_id: string;
  conversation_id: string | null;
  channel: string;
  direction: 'inbound' | 'outbound';
  body: string;
  status: string;
  ai_generated: boolean;
  created_at: string;
}

// ============ API Functions ============

export const subAccountsApi = {
  list: () => api.get<SubAccount[]>('/sub-accounts/'),
  get: (id: string) => api.get<SubAccount>(`/sub-accounts/${id}`),
  create: (data: Partial<SubAccount>) => api.post<SubAccount>('/sub-accounts/', data),
  update: (id: string, data: Partial<SubAccount>) =>
    api.patch<SubAccount>(`/sub-accounts/${id}`, data),
  delete: (id: string) => api.delete(`/sub-accounts/${id}`),
};

export const contactsApi = {
  list: (params?: { search?: string; tag?: string; status?: string }) =>
    api.get<Contact[]>('/contacts/', { params }),
  get: (id: string) => api.get<Contact>(`/contacts/${id}`),
  create: (data: Partial<Contact>) => api.post<Contact>('/contacts/', data),
  update: (id: string, data: Partial<Contact>) =>
    api.patch<Contact>(`/contacts/${id}`, data),
  delete: (id: string) => api.delete(`/contacts/${id}`),
  notes: (id: string) => api.get<Note[]>(`/contacts/${id}/notes`),
  addNote: (id: string, body: string) =>
    api.post<Note>(`/contacts/${id}/notes`, { body }),
};

export const conversationsApi = {
  list: (status?: string) =>
    api.get<Conversation[]>('/conversations/', { params: { status } }),
  get: (id: string) => api.get<Conversation>(`/conversations/${id}`),
  messages: (conversationId: string) =>
    api.get<Message[]>(`/conversations/${conversationId}/messages`),
  setStatus: (id: string, status: string) =>
    api.patch(`/conversations/${id}/status`, null, { params: { status } }),
  toggleAi: (id: string, enabled: boolean) =>
    api.patch(`/conversations/${id}/ai`, null, { params: { enabled } }),
};

export const messagesApi = {
  send: (data: { contact_id: string; channel?: string; body: string }) =>
    api.post<Message>('/messages/send', data),
};
