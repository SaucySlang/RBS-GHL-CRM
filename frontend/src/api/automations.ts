import { api } from './client';

export type StepType = 'send_sms' | 'send_email' | 'wait' | 'notify_owner';

export type ExecutionState =
  | 'PENDING'
  | 'COMPLETED'
  | 'FAILED'
  | 'SKIPPED_COMPLIANCE'
  | 'PAUSED_QUIET_HOURS';

export interface WorkflowStep {
  id: string;
  order: number;
  step_type: StepType;
  config: Record<string, unknown>;
}

export interface Workflow {
  id: string;
  sub_account_id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  is_active: boolean;
  steps: WorkflowStep[];
  created_at: string;
  updated_at: string;
}

export interface ExecutionLog {
  id: string;
  execution_id: string;
  workflow_id: string;
  step_id: string | null;
  contact_id: string | null;
  state: ExecutionState;
  detail: string | null;
  scheduled_for: string;
  created_at: string;
  completed_at: string | null;
}

export const automationsApi = {
  list: () => api.get<Workflow[]>('/automations/'),
  create: (data: {
    name: string;
    trigger_type: string;
    steps: { step_type: StepType; config: Record<string, unknown> }[];
  }) => api.post<Workflow>('/automations/', data),
  createSpeedToLead: () => api.post<Workflow>('/automations/speed-to-lead'),
  update: (id: string, data: Partial<Workflow>) =>
    api.patch<Workflow>(`/automations/${id}`, data),
  delete: (id: string) => api.delete(`/automations/${id}`),
  logs: (params?: { workflow_id?: string; state?: ExecutionState }) =>
    api.get<ExecutionLog[]>('/automations/logs', { params }),
};
