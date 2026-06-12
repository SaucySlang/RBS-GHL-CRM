import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { Plus, DollarSign, X, HeartCrack } from 'lucide-react';
import { dealsApi, Deal, DealStage } from '../api/deals';
import { wsUrl } from '../api/client';
import { useSubAccountStore } from '../store/subAccountStore';

const STAGES: { id: DealStage; label: string; tint: string }[] = [
  { id: 'new_lead', label: 'New Lead', tint: 'text-sky-400' },
  { id: 'contacted', label: 'Contacted', tint: 'text-indigo-400' },
  { id: 'qualified', label: 'Qualified', tint: 'text-accent' },
  { id: 'proposal_sent', label: 'Proposal Sent', tint: 'text-amber-400' },
  { id: 'won', label: 'Won', tint: 'text-emerald-400' },
  { id: 'lost', label: 'Lost', tint: 'text-rose-400' },
];

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

export function PipelinePage() {
  const queryClient = useQueryClient();
  const activeSubAccountId = useSubAccountStore((s) => s.activeSubAccountId);
  const [activeDeal, setActiveDeal] = useState<Deal | null>(null);
  const [pendingLost, setPendingLost] = useState<{ deal: Deal; position: number } | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  const { data: deals } = useQuery({
    queryKey: ['deals'],
    queryFn: () => dealsApi.list(),
    select: (res) => res.data,
    enabled: !!activeSubAccountId,
  });

  // ---- Real-time sync: any change in another tab patches this cache ----
  const wsRef = useRef<WebSocket | null>(null);
  useEffect(() => {
    if (!activeSubAccountId) return;
    const ws = new WebSocket(wsUrl(`/ws/pipeline?sub_account_id=${activeSubAccountId}`));
    wsRef.current = ws;
    ws.onmessage = (evt) => {
      const event = JSON.parse(evt.data) as { type: string; deal: Deal & { id: string } };
      queryClient.setQueryData<{ data: Deal[] } | undefined>(['deals'], (old) => {
        if (!old) return old;
        let next = old.data.filter((d) => d.id !== event.deal.id);
        if (event.type !== 'deal_deleted') next = [...next, event.deal as Deal];
        return { ...old, data: next };
      });
    };
    const keepAlive = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send('ping');
    }, 25_000);
    return () => {
      clearInterval(keepAlive);
      ws.close();
    };
  }, [activeSubAccountId, queryClient]);

  const moveMutation = useMutation({
    mutationFn: ({ id, stage, position, lost_reason }: {
      id: string; stage: DealStage; position: number; lost_reason?: string;
    }) => dealsApi.move(id, { stage, position, lost_reason }),
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['deals'] }),
  });

  const byStage = useMemo(() => {
    const map = new Map<DealStage, Deal[]>(STAGES.map((s) => [s.id, []]));
    (deals ?? [])
      .slice()
      .sort((a, b) => a.position - b.position || a.created_at.localeCompare(b.created_at))
      .forEach((d) => map.get(d.stage)?.push(d));
    return map;
  }, [deals]);

  const applyOptimisticMove = useCallback(
    (dealId: string, stage: DealStage, position: number) => {
      queryClient.setQueryData<{ data: Deal[] } | undefined>(['deals'], (old) => {
        if (!old) return old;
        return {
          ...old,
          data: old.data.map((d) => (d.id === dealId ? { ...d, stage, position } : d)),
        };
      });
    },
    [queryClient]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  const onDragStart = (event: DragStartEvent) => {
    const deal = deals?.find((d) => d.id === event.active.id);
    setActiveDeal(deal ?? null);
  };

  const onDragEnd = (event: DragEndEvent) => {
    setActiveDeal(null);
    const { active, over } = event;
    if (!over || !deals) return;

    const deal = deals.find((d) => d.id === active.id);
    if (!deal) return;
    const targetStage = over.id as DealStage;
    if (!STAGES.some((s) => s.id === targetStage) || targetStage === deal.stage) return;

    const column = byStage.get(targetStage) ?? [];
    const position = column.length ? Math.max(...column.map((d) => d.position)) + 1 : 1;

    if (targetStage === 'lost') {
      // Sleek modal demanding a reason before the database is touched
      setPendingLost({ deal, position });
      return;
    }

    applyOptimisticMove(deal.id, targetStage, position);
    moveMutation.mutate({ id: deal.id, stage: targetStage, position });
  };

  const confirmLost = (reason: string) => {
    if (!pendingLost) return;
    applyOptimisticMove(pendingLost.deal.id, 'lost', pendingLost.position);
    moveMutation.mutate({
      id: pendingLost.deal.id,
      stage: 'lost',
      position: pendingLost.position,
      lost_reason: reason,
    });
    setPendingLost(null);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-edge">
        <div>
          <h2 className="text-lg font-semibold text-white">Deal Pipeline</h2>
          <p className="text-xs text-gray-500">
            Drag cards between stages · changes sync live across tabs
          </p>
        </div>
        <button className="btn-primary flex items-center gap-1.5" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> New Deal
        </button>
      </div>

      <DndContext sensors={sensors} onDragStart={onDragStart} onDragEnd={onDragEnd}>
        <div className="flex-1 overflow-x-auto">
          <div className="flex gap-3 p-4 h-full min-w-max">
            {STAGES.map((stage) => (
              <StageColumn
                key={stage.id}
                stage={stage}
                deals={byStage.get(stage.id) ?? []}
              />
            ))}
          </div>
        </div>
        <DragOverlay>
          {activeDeal && <DealCard deal={activeDeal} overlay />}
        </DragOverlay>
      </DndContext>

      {pendingLost && (
        <LostReasonModal
          dealTitle={pendingLost.deal.title}
          onCancel={() => setPendingLost(null)}
          onConfirm={confirmLost}
        />
      )}
      {showCreate && <CreateDealModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function StageColumn({
  stage,
  deals,
}: {
  stage: { id: DealStage; label: string; tint: string };
  deals: Deal[];
}) {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id });
  const total = deals.reduce((sum, d) => sum + Number(d.value || 0), 0);

  return (
    <div
      ref={setNodeRef}
      className={`w-72 flex flex-col card transition ${
        isOver ? 'border-primary/70 shadow-glow' : ''
      }`}
    >
      <div className="px-4 py-3 border-b border-edge flex items-center justify-between">
        <p className={`text-sm font-semibold ${stage.tint}`}>{stage.label}</p>
        <p className="text-[11px] text-gray-500">
          {deals.length} · {currency.format(total)}
        </p>
      </div>
      <div className="flex-1 overflow-y-auto p-2.5 space-y-2.5">
        {deals.map((deal) => (
          <DraggableDealCard key={deal.id} deal={deal} />
        ))}
        {deals.length === 0 && (
          <p className="text-center text-xs text-gray-600 py-6">Drop deals here</p>
        )}
      </div>
    </div>
  );
}

function DraggableDealCard({ deal }: { deal: Deal }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: deal.id,
  });

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={{ transform: CSS.Translate.toString(transform) }}
      className={isDragging ? 'opacity-30' : ''}
    >
      <DealCard deal={deal} />
    </div>
  );
}

function DealCard({ deal, overlay = false }: { deal: Deal; overlay?: boolean }) {
  return (
    <div
      className={`bg-surface-overlay border border-edge rounded-lg px-3.5 py-3 cursor-grab active:cursor-grabbing transition hover:border-primary/60 ${
        overlay ? 'shadow-glow border-primary/70 rotate-2' : ''
      }`}
    >
      <p className="text-sm font-medium text-white leading-snug">{deal.title}</p>
      <p className="text-xs text-accent mt-1.5 flex items-center gap-1">
        <DollarSign size={12} />
        {currency.format(Number(deal.value || 0))}
      </p>
      {deal.stage === 'lost' && deal.lost_reason && (
        <p className="text-[11px] text-rose-400/80 mt-1.5 italic line-clamp-2">
          “{deal.lost_reason}”
        </p>
      )}
    </div>
  );
}

function LostReasonModal({
  dealTitle,
  onCancel,
  onConfirm,
}: {
  dealTitle: string;
  onCancel: () => void;
  onConfirm: (reason: string) => void;
}) {
  const [reason, setReason] = useState('');

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="card bg-surface-overlay w-[440px] p-6 border-rose-900/50">
        <div className="flex items-center gap-3 mb-1">
          <span className="w-9 h-9 rounded-lg bg-rose-500/15 text-rose-400 flex items-center justify-center">
            <HeartCrack size={18} />
          </span>
          <div>
            <h3 className="text-base font-semibold text-white">Mark deal as Lost</h3>
            <p className="text-xs text-gray-500">“{dealTitle}”</p>
          </div>
        </div>
        <p className="text-sm text-gray-400 mt-3">
          A lost reason is required before this change is saved.
        </p>
        <textarea
          autoFocus
          className="input w-full mt-3 h-24 resize-none"
          placeholder="e.g. Went with a competitor, budget cut, no response after 5 touches…"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <div className="flex justify-end gap-2 mt-4">
          <button className="btn-ghost" onClick={onCancel}>
            Keep in pipeline
          </button>
          <button
            className="btn-primary bg-rose-600 hover:bg-rose-500"
            disabled={!reason.trim()}
            onClick={() => onConfirm(reason.trim())}
          >
            Mark Lost
          </button>
        </div>
      </div>
    </div>
  );
}

function CreateDealModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('');
  const [value, setValue] = useState('');
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: () => dealsApi.create({ title: title.trim(), value: Number(value) || 0 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="card bg-surface-overlay w-[420px] p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-white">New Deal</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <input
          autoFocus
          className="input w-full"
          placeholder="Deal title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <input
          className="input w-full mt-3"
          placeholder="Value (USD)"
          type="number"
          min="0"
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
        <div className="flex justify-end gap-2 mt-5">
          <button className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn-primary"
            disabled={!title.trim() || createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
}
