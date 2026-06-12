import { api } from './client';

export interface FormField {
  key: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'textarea' | 'hidden';
  required: boolean;
  enabled: boolean;
}

export interface FormConfig {
  submit_label: string;
  success_message: string;
  theme: { background: string; accent: string; text: string };
}

export interface LeadForm {
  id: string;
  sub_account_id: string;
  name: string;
  fields_json: FormField[];
  configurations_json: FormConfig;
  is_published: boolean;
  submission_count: number;
  created_at: string;
  updated_at: string;
}

export interface EmbedInfo {
  form_id: string;
  embed_url: string;
  snippet: string;
}

export const formsApi = {
  list: () => api.get<LeadForm[]>('/forms/'),
  get: (id: string) => api.get<LeadForm>(`/forms/${id}`),
  create: (data: { name: string }) => api.post<LeadForm>('/forms/', data),
  update: (id: string, data: Partial<LeadForm>) => api.patch<LeadForm>(`/forms/${id}`, data),
  delete: (id: string) => api.delete(`/forms/${id}`),
  embed: (id: string) => api.get<EmbedInfo>(`/forms/${id}/embed`),
};
