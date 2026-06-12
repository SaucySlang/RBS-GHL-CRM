import { api } from './client';

export type DealStage =
  | 'new_lead'
  | 'contacted'
  | 'qualified'
  | 'proposal_sent'
  | 'won'
  | 'lost';

export interface Deal {
  id: string;
  sub_account_id: string;
  contact_id: string | null;
  title: string;
  value: number | string;
  stage: DealStage;
  lost_reason: string | null;
  position: number;
  created_at: string;
  updated_at: string;
}

export const dealsApi = {
  list: (stage?: DealStage) => api.get<Deal[]>('/deals/', { params: { stage } }),
  create: (data: { title: string; value?: number; contact_id?: string; stage?: DealStage }) =>
    api.post<Deal>('/deals/', data),
  update: (id: string, data: Partial<Deal>) => api.patch<Deal>(`/deals/${id}`, data),
  move: (id: string, data: { stage: DealStage; position: number; lost_reason?: string }) =>
    api.post<Deal>(`/deals/${id}/move`, data),
  delete: (id: string) => api.delete(`/deals/${id}`),
};
