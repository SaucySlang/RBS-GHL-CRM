import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Zap, MessageSquare, Mail, Clock, BellRing, ChevronRight, Trash2, ShieldOff, MoonStar,
} from 'lucide-react';
import {
  automationsApi, Workflow, StepType, ExecutionState,
} from '../api/automations';

const STEP_META: Record<StepType, { icon: typeof Zap; label: string }> = {
  send_sms: { icon: MessageSquare, label: 'SMS' },
  send_email: { icon: Mail, label: 'Email' },
  wait: { icon: Clock, label: 'Wait' },
  notify_owner: { icon: BellRing, label: 'Notify Owner' },
};

const STATE_STYLES: Record<ExecutionState, string> = {
  PENDING: 'bg-sky-500/15 text-sky-400',
  COMPLETED: 'bg-emerald-500/15 text-emerald-400',
  FAILED: 'bg-rose-500/15 text-rose-400',
  SKIPPED_COMPLIANCE: 'bg-amber-500/15 text-amber-400',
  PAUSED_QUIET_HOURS: 'bg-indigo-500/15 text-indigo-400',
};

export function AutomationsPage() {
  const queryClient = useQueryClient();

  const { data: workflows } = useQuery({
    queryKey: ['automations'],
    queryFn: () => automationsApi.list(),
    select: (res) => res.data,
  });

  const { data: logs } = useQuery({
    queryKey: ['automation-logs'],
    queryFn: () => automationsApi.logs(),
    select: (res) => res.data,
    refetchInterval: 5_000,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['automations'] });

  const speedToLeadMutation = useMutation({
    mutationFn: () => automationsApi.createSpeedToLead(),
    onSuccess: invalidate,
  });
  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      automationsApi.update(id, { is_active }),
    onSuccess: invalidate,
  });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => automationsApi.delete(id),
    onSuccess: invalidate,
  });

  return (
    <div className="p-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Automation Workflows</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Speed-to-lead sequences with A2P compliance guard and quiet-hours windows
          </p>
        </div>
        <button
          className="btn-primary flex items-center gap-1.5"
          onClick={() => speedToLeadMutation.mutate()}
        >
          <Zap size={15} /> New Speed-to-Lead
        </button>
      </div>

      <div className="space-y-3 mt-5">
        {workflows?.length === 0 && (
          <p className="text-sm text-gray-500 card p-5">
            No workflows in this workspace yet.
          </p>
        )}
        {workflows?.map((wf) => (
          <WorkflowCard
            key={wf.id}
            workflow={wf}
            onToggle={() => toggleMutation.mutate({ id: wf.id, is_active: !wf.is_active })}
            onDelete={() => deleteMutation.mutate(wf.id)}
          />
        ))}
      </div>

      <div className="card mt-8">
        <div className="px-5 py-4 border-b border-edge">
          <h3 className="text-sm font-semibold text-white">Execution Log</h3>
          <p className="text-[11px] text-gray-500 mt-0.5 flex items-center gap-3">
            <span className="flex items-center gap-1">
              <ShieldOff size={11} className="text-amber-400" /> compliance skips
            </span>
            <span className="flex items-center gap-1">
              <MoonStar size={11} className="text-indigo-400" /> quiet-hours pauses
            </span>
          </p>
        </div>
        <div className="max-h-96 overflow-auto">
          {logs?.length === 0 && (
            <p className="p-4 text-sm text-gray-600">No executions yet.</p>
          )}
          {logs?.map((log) => (
            <div
              key={log.id}
              className="px-5 py-2.5 border-b border-edge/50 flex items-center gap-3"
            >
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded ${STATE_STYLES[log.state]}`}
              >
                {log.state}
              </span>
              <span className="text-xs text-gray-400 flex-1 truncate">
                {log.detail ?? '—'}
              </span>
              <span className="text-[11px] text-gray-600 whitespace-nowrap">
                {new Date(log.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function WorkflowCard({
  workflow,
  onToggle,
  onDelete,
}: {
  workflow: Workflow;
  onToggle: () => void;
  onDelete: () => void;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-white">{workflow.name}</p>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Trigger: <span className="text-accent">{workflow.trigger_type}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onToggle}
            className={`text-[11px] px-2.5 py-1 rounded-lg border transition ${
              workflow.is_active
                ? 'border-emerald-700 text-emerald-400 bg-emerald-500/10'
                : 'border-edge text-gray-500'
            }`}
          >
            {workflow.is_active ? 'Active' : 'Paused'}
          </button>
          <button
            onClick={onDelete}
            className="text-gray-600 hover:text-rose-400 transition"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>

      {/* Step chain visualization */}
      <div className="flex items-center gap-1.5 mt-4 flex-wrap">
        <span className="text-[11px] px-2 py-1 rounded bg-primary/15 text-accent border border-primary/30">
          {workflow.trigger_type === 'form_submission' ? 'Form Submission' : workflow.trigger_type}
        </span>
        {workflow.steps.map((step) => {
          const meta = STEP_META[step.step_type];
          const Icon = meta.icon;
          const waitSeconds =
            step.step_type === 'wait' ? Number(step.config.seconds ?? 60) : null;
          return (
            <span key={step.id} className="flex items-center gap-1.5">
              <ChevronRight size={13} className="text-gray-600" />
              <span className="text-[11px] px-2 py-1 rounded bg-surface-overlay border border-edge text-gray-300 flex items-center gap-1.5">
                <Icon size={11} className="text-primary" />
                {meta.label}
                {waitSeconds !== null && ` ${waitSeconds}s`}
              </span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
