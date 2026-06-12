/**
 * LeadStack CRM — Claude.design drop-in
 * =====================================
 * Single-file, dependency-light replica of the production frontend design.
 * Drop this file into Claude.design (or any React + Tailwind sandbox) as-is.
 *
 * - Only dependencies: react, lucide-react, Tailwind utility classes.
 * - No router / react-query / zustand / backend — all data is mocked,
 *   navigation is local state. Functionality in the real app is untouched.
 * - Design tokens mirror frontend/src/index.css exactly (hex literals here,
 *   CSS variables in production). Map any redesign back via these tokens:
 *
 *     surface        #08080d   page background
 *     surface-raised #0f0f18   cards / panels        -> .card
 *     surface-overlay#181826   modals / dropdowns
 *     edge           #2a2a3e   crisp borders
 *     primary        #8b5cf6   violet-500 brand
 *     accent         #c084fc   purple-400 highlights
 *
 * Screens included: Pipeline (Kanban + lost-reason modal), Contacts,
 * Conversations, Forms builder, Automations, AI Receptionist, Branding,
 * and the public Landing page (condensed).
 */
import { useMemo, useState } from 'react';
import {
  ArrowRight, Ban, BellRing, Bot, Building2, Check, ChevronDown,
  ChevronRight, ChevronsUpDown, Clock, Code2, Copy, DollarSign, Eye,
  FormInput, Globe, Globe2, GripVertical, HeartCrack, KanbanSquare, Mail,
  MessageSquare, MoonStar, Palette, Phone, Plus, Rocket, Search, Send,
  ShieldCheck, ShieldOff, Sparkles, StickyNote, Trash2, UserCheck, Users,
  Workflow, X, Zap,
} from 'lucide-react';

/* ================================ tokens ================================ */

const T = {
  surface: '#08080d',
  raised: '#0f0f18',
  overlay: '#181826',
  edge: '#2a2a3e',
  primary: '#8b5cf6',
  accent: '#c084fc',
};

const card =
  'rounded-xl border border-[#2a2a3e] bg-[#0f0f18] bg-gradient-to-br from-white/[0.025] to-transparent shadow-[0_1px_2px_rgba(0,0,0,0.4),0_8px_24px_-12px_rgba(0,0,0,0.5)]';
const input =
  'rounded-lg border border-[#2a2a3e] bg-[#08080d]/80 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 shadow-[inset_0_1px_2px_rgba(0,0,0,0.3)] outline-none transition focus:border-violet-500/60 focus:ring-2 focus:ring-violet-500/50';
const btnPrimary =
  'rounded-lg px-4 py-2 text-sm font-medium text-white transition bg-gradient-to-b from-violet-500/95 to-violet-500/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.15),0_2px_10px_-2px_rgba(139,92,246,0.5)] hover:brightness-110 hover:shadow-[0_4px_18px_-2px_rgba(139,92,246,0.65)] active:translate-y-px disabled:opacity-50 disabled:cursor-not-allowed';
const btnGhost =
  'rounded-lg border border-[#2a2a3e] px-4 py-2 text-sm font-medium text-gray-300 transition hover:border-violet-500/60 hover:bg-violet-500/5 hover:text-white';
const panelLabel = 'text-[11px] uppercase tracking-wider text-gray-500';

/* ============================== mock data =============================== */

const WORKSPACES = [
  { id: 'ws-1', name: 'Real Estate', industry: 'Real Estate' },
  { id: 'ws-2', name: 'Music Production Studio', industry: 'Music Production' },
  { id: 'ws-3', name: 'E-commerce Brands', industry: 'E-commerce' },
  { id: 'ws-4', name: 'AI Consulting', industry: 'AI Consulting' },
];

const STAGES = [
  { id: 'new_lead', label: 'New Lead', tint: 'text-sky-400' },
  { id: 'contacted', label: 'Contacted', tint: 'text-indigo-400' },
  { id: 'qualified', label: 'Qualified', tint: 'text-[#c084fc]' },
  { id: 'proposal_sent', label: 'Proposal Sent', tint: 'text-amber-400' },
  { id: 'won', label: 'Won', tint: 'text-emerald-400' },
  { id: 'lost', label: 'Lost', tint: 'text-rose-400' },
];

const DEALS = [
  { id: 'd1', title: 'Downtown duplex inquiry', value: 8400, stage: 'new_lead' },
  { id: 'd2', title: 'EP mixing — 6 tracks', value: 2200, stage: 'new_lead' },
  { id: 'd3', title: 'Shopify migration', value: 5800, stage: 'qualified' },
  { id: 'd4', title: 'AI chatbot rollout', value: 12000, stage: 'proposal_sent' },
  { id: 'd5', title: 'Listing: 14 Cedar Ln', value: 9750, stage: 'proposal_sent' },
  { id: 'd6', title: 'Studio block — March', value: 3600, stage: 'won' },
  { id: 'd7', title: 'Wedding videography', value: 1800, stage: 'lost', lost_reason: 'Went with a competitor' },
];

const CONTACTS = [
  { id: 'c1', name: 'Sarah Connor', email: 'sarah@example.com', phone: '+1 (555) 123-4567', source: 'ai_receptionist', tags: ['hot-lead'], dnd: false },
  { id: 'c2', name: 'Jamie Rivera', email: 'jamie@example.com', phone: '+1 (555) 777-0001', source: 'form', tags: ['beat-pack', 'follow-up'], dnd: false },
  { id: 'c3', name: 'Devon Okafor', email: 'devon@example.com', phone: '+1 (555) 999-0000', source: 'sms_inbound', tags: [], dnd: true },
];

const FORM_FIELDS = [
  { key: 'first_name', label: 'First Name', type: 'text', required: true },
  { key: 'last_name', label: 'Last Name', type: 'text', required: false },
  { key: 'email', label: 'Email', type: 'email', required: true },
  { key: 'phone', label: 'Phone', type: 'tel', required: false },
  { key: 'message', label: 'Message', type: 'textarea', required: false },
  { key: 'sub_account_id', label: 'Sub-Account ID', type: 'hidden', required: true },
];

const EXEC_LOGS = [
  { state: 'COMPLETED', detail: 'Sent sms message 82f71647', at: '2:41 PM' },
  { state: 'COMPLETED', detail: 'Sent email message 1ad3aed3', at: '2:41 PM' },
  { state: 'COMPLETED', detail: 'Waited node: next step in 60s', at: '2:42 PM' },
  { state: 'PENDING', detail: 'Owner notification queued', at: '2:42 PM' },
  { state: 'SKIPPED_COMPLIANCE', detail: 'Phone number is in the opt-out registry (A2P compliance)', at: '1:17 PM' },
  { state: 'PAUSED_QUIET_HOURS', detail: 'Outside send window; resuming at 08:00 local', at: '11:54 PM' },
];

const STATE_STYLES = {
  PENDING: 'bg-sky-500/15 text-sky-400',
  COMPLETED: 'bg-emerald-500/15 text-emerald-400',
  FAILED: 'bg-rose-500/15 text-rose-400',
  SKIPPED_COMPLIANCE: 'bg-amber-500/15 text-amber-400',
  PAUSED_QUIET_HOURS: 'bg-indigo-500/15 text-indigo-400',
};

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

/* ================================= app ================================== */

const NAV = [
  { id: 'pipeline', icon: KanbanSquare, label: 'Pipeline' },
  { id: 'contacts', icon: Users, label: 'Contacts' },
  { id: 'conversations', icon: MessageSquare, label: 'Conversations' },
  { id: 'forms', icon: FormInput, label: 'Forms' },
  { id: 'automations', icon: Zap, label: 'Automations' },
  { id: 'receptionist', icon: Bot, label: 'AI Receptionist' },
  { id: 'branding', icon: Palette, label: 'Branding' },
  { id: 'landing', icon: Globe, label: 'Landing Page' },
];

export default function App() {
  const [screen, setScreen] = useState('pipeline');

  if (screen === 'landing') {
    return (
      <div className="font-sans">
        <button
          onClick={() => setScreen('pipeline')}
          className="fixed bottom-4 right-4 z-50 rounded-full bg-violet-600 px-4 py-2 text-xs font-semibold text-white shadow-[0_0_24px_rgba(139,92,246,0.5)]"
        >
          ← Back to app
        </button>
        <Landing />
      </div>
    );
  }

  return (
    <div className="flex h-screen font-sans text-gray-200" style={{ background: T.surface }}>
      <Sidebar screen={screen} setScreen={setScreen} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <main
          className="flex-1 overflow-auto"
          style={{ backgroundImage: 'radial-gradient(55% 35% at 50% 0%, rgba(139,92,246,0.07) 0%, transparent 70%)' }}
        >
          {screen === 'pipeline' && <Pipeline />}
          {screen === 'contacts' && <Contacts />}
          {screen === 'conversations' && <Conversations />}
          {screen === 'forms' && <Forms />}
          {screen === 'automations' && <Automations />}
          {screen === 'receptionist' && <Receptionist />}
          {screen === 'branding' && <Branding />}
        </main>
      </div>
    </div>
  );
}

/* ================================ shell ================================= */

function Sidebar({ screen, setScreen }) {
  return (
    <aside className="flex w-60 flex-col border-r border-[#2a2a3e] bg-[#0f0f18]/40">
      <div className="flex items-center gap-3 border-b border-[#2a2a3e] px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-500/20 text-violet-400 shadow-[0_0_12px_rgba(139,92,246,0.25)]">
          <Sparkles size={16} />
        </span>
        <div>
          <h1 className="text-base font-bold tracking-tight text-white">
            <span className="text-violet-400">Lead</span>Stack
          </h1>
          <p className="mt-0.5 text-[10px] uppercase tracking-widest text-gray-500">Own your platform</p>
        </div>
      </div>
      <nav className="mt-4 flex-1 space-y-0.5 px-2.5">
        <p className={`${panelLabel} px-2.5 pb-2`}>Workspace</p>
        {NAV.map(({ id, icon: Icon, label }) => {
          const active = screen === id;
          return (
            <button
              key={id}
              onClick={() => setScreen(id)}
              className={`group relative flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition ${
                active
                  ? 'bg-violet-500/15 text-white shadow-[0_0_12px_rgba(139,92,246,0.25)]'
                  : 'text-gray-400 hover:bg-white/[0.04] hover:text-white'
              }`}
            >
              <span
                className={`absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full transition ${
                  active ? 'bg-violet-500' : 'bg-transparent group-hover:bg-[#2a2a3e]'
                }`}
              />
              <Icon size={16} className={active ? 'text-violet-400' : 'text-gray-500 group-hover:text-gray-300'} />
              {label}
            </button>
          );
        })}
      </nav>
      <div className="m-3 rounded-xl border border-[#2a2a3e] bg-[#08080d]/60 px-3.5 py-3">
        <p className="text-[11px] font-medium text-gray-300">4 isolated workspaces</p>
        <p className="mt-0.5 text-[10px] leading-relaxed text-gray-600">Data never crosses between businesses.</p>
      </div>
    </aside>
  );
}

function TopBar() {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(WORKSPACES[0]);
  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-[#2a2a3e] bg-[#08080d]/70 px-6 backdrop-blur-md">
      <div className="relative">
        <button
          onClick={() => setOpen((v) => !v)}
          className={`${card} flex min-w-[220px] items-center gap-2.5 px-3 py-2 transition hover:border-violet-500/60`}
        >
          <span className="flex h-6 w-6 items-center justify-center rounded bg-violet-500/20 text-violet-400">
            <Building2 size={14} />
          </span>
          <span className="flex-1 text-left">
            <span className="block text-sm font-medium leading-tight text-white">{active.name}</span>
            <span className="block text-[11px] leading-tight text-gray-500">{active.industry}</span>
          </span>
          <ChevronsUpDown size={15} className="text-gray-500" />
        </button>
        {open && (
          <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-[#2a2a3e] bg-[#181826] shadow-[0_0_24px_rgba(139,92,246,0.35)]">
            <p className="px-3 pb-1 pt-2.5 text-[10px] uppercase tracking-widest text-gray-500">Workspaces</p>
            {WORKSPACES.map((ws) => (
              <button
                key={ws.id}
                onClick={() => { setActive(ws); setOpen(false); }}
                className="flex w-full items-center gap-2.5 px-3 py-2.5 text-left transition hover:bg-violet-500/10"
              >
                <span className="flex h-6 w-6 items-center justify-center rounded bg-violet-500/20 text-violet-400">
                  <Building2 size={13} />
                </span>
                <span className="flex-1">
                  <span className="block text-sm text-gray-200">{ws.name}</span>
                  <span className="block text-[11px] text-gray-500">{ws.industry}</span>
                </span>
                {ws.id === active.id && <Check size={15} className="text-violet-400" />}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="hidden items-center gap-2 text-xs text-gray-500 md:flex">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
        All data below is isolated to the selected workspace
      </div>
    </header>
  );
}

/* =============================== pipeline =============================== */

function Pipeline() {
  const [showLost, setShowLost] = useState(false);
  const byStage = useMemo(
    () => STAGES.map((s) => ({ ...s, deals: DEALS.filter((d) => d.stage === s.id) })),
    []
  );
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-[#2a2a3e] px-6 py-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Deal Pipeline</h2>
          <p className="text-xs text-gray-500">Drag cards between stages · changes sync live across tabs</p>
        </div>
        <div className="flex gap-2">
          <button className={btnGhost} onClick={() => setShowLost(true)}>Preview Lost modal</button>
          <button className={`${btnPrimary} flex items-center gap-1.5`}><Plus size={16} /> New Deal</button>
        </div>
      </div>
      <div className="flex-1 overflow-x-auto">
        <div className="flex h-full min-w-max gap-3 p-4">
          {byStage.map((stage) => (
            <div key={stage.id} className={`${card} flex w-72 flex-col`}>
              <div className="flex items-center justify-between border-b border-[#2a2a3e] px-4 py-3">
                <p className={`text-sm font-semibold ${stage.tint}`}>{stage.label}</p>
                <p className="text-[11px] text-gray-500">
                  {stage.deals.length} · {currency.format(stage.deals.reduce((s, d) => s + d.value, 0))}
                </p>
              </div>
              <div className="flex-1 space-y-2.5 overflow-y-auto p-2.5">
                {stage.deals.map((deal) => (
                  <div
                    key={deal.id}
                    className="cursor-grab rounded-lg border border-[#2a2a3e] bg-[#181826] px-3.5 py-3 transition hover:border-violet-500/60 active:cursor-grabbing"
                  >
                    <p className="text-sm font-medium leading-snug text-white">{deal.title}</p>
                    <p className="mt-1.5 flex items-center gap-1 text-xs text-[#c084fc]">
                      <DollarSign size={12} />{currency.format(deal.value)}
                    </p>
                    {deal.lost_reason && (
                      <p className="mt-1.5 text-[11px] italic text-rose-400/80">“{deal.lost_reason}”</p>
                    )}
                  </div>
                ))}
                {stage.deals.length === 0 && (
                  <p className="py-6 text-center text-xs text-gray-600">Drop deals here</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      {showLost && <LostModal onClose={() => setShowLost(false)} />}
    </div>
  );
}

function LostModal({ onClose }) {
  const [reason, setReason] = useState('');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className={`${card} w-[440px] !border-rose-900/50 bg-[#181826] p-6`}>
        <div className="mb-1 flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-500/15 text-rose-400">
            <HeartCrack size={18} />
          </span>
          <div>
            <h3 className="text-base font-semibold text-white">Mark deal as Lost</h3>
            <p className="text-xs text-gray-500">“AI chatbot rollout”</p>
          </div>
        </div>
        <p className="mt-3 text-sm text-gray-400">A lost reason is required before this change is saved.</p>
        <textarea
          autoFocus
          className={`${input} mt-3 h-24 w-full resize-none`}
          placeholder="e.g. Went with a competitor, budget cut, no response after 5 touches…"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <div className="mt-4 flex justify-end gap-2">
          <button className={btnGhost} onClick={onClose}>Keep in pipeline</button>
          <button
            className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-500 disabled:opacity-50"
            disabled={!reason.trim()}
            onClick={onClose}
          >
            Mark Lost
          </button>
        </div>
      </div>
    </div>
  );
}

/* =============================== contacts =============================== */

function Contacts() {
  const [selected, setSelected] = useState(CONTACTS[0]);
  return (
    <div className="flex h-full">
      <div className="flex w-96 flex-col border-r border-[#2a2a3e]">
        <div className="flex gap-2 border-b border-[#2a2a3e] p-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 text-gray-500" size={17} />
            <input className={`${input} w-full pl-10`} placeholder="Search contacts..." />
          </div>
          <button className={`${btnPrimary} px-2.5`}><Plus size={18} /></button>
        </div>
        <div className="flex-1 overflow-auto">
          {CONTACTS.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelected(c)}
              className={`w-full border-b border-[#2a2a3e]/60 px-4 py-3 text-left transition hover:bg-[#0f0f18] ${
                selected.id === c.id ? 'bg-violet-500/10' : ''
              }`}
            >
              <p className="flex items-center gap-2 text-sm font-medium text-white">
                {c.name}
                {c.dnd && <Ban size={13} className="text-red-400" />}
              </p>
              <p className="mt-0.5 text-xs text-gray-500">{c.email}</p>
              {c.tags.length > 0 && (
                <span className="mt-1.5 inline-flex flex-wrap gap-1">
                  {c.tags.map((t) => (
                    <span key={t} className="rounded bg-violet-500/15 px-1.5 py-0.5 text-[10px] text-[#c084fc]">{t}</span>
                  ))}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">{selected.name}</h2>
              <p className="mt-1 text-xs text-gray-500">Source: {selected.source} · Created 6/12/2026</p>
            </div>
            <button className={`${btnGhost} !border-rose-900/60 !text-rose-400 hover:!border-rose-500`}><Trash2 size={15} /></button>
          </div>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className={`${card} p-4`}>
              <p className={`${panelLabel} flex items-center gap-1.5`}><Phone size={12} /> Phone</p>
              <p className="mt-1 text-sm text-gray-200">{selected.phone}</p>
            </div>
            <div className={`${card} p-4`}>
              <p className={`${panelLabel} flex items-center gap-1.5`}><Mail size={12} /> Email</p>
              <p className="mt-1 text-sm text-gray-200">{selected.email}</p>
            </div>
          </div>
          <div className={`${card} mt-4 p-4`}>
            <p className={`${panelLabel} mb-3 flex items-center gap-1.5`}><StickyNote size={12} /> Notes</p>
            <div className="mb-3 flex gap-2">
              <input className={`${input} flex-1`} placeholder="Add a note…" />
              <button className={btnPrimary}>Add</button>
            </div>
            <div className="border-t border-[#2a2a3e]/60 py-2.5">
              <p className="text-sm text-gray-300">Asked about pricing for the spring campaign — wants a call Thursday.</p>
              <p className="mt-1 text-[11px] text-gray-600">6/12/2026, 1:42 PM</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================ conversations ============================= */

function Conversations() {
  const msgs = [
    { dir: 'in', body: 'Hey! Do you have any studio availability in March?', ai: false },
    { dir: 'out', body: "Hi! Yes — we have open blocks the weeks of March 9 and 23. Are you tracking a full project or single sessions?", ai: true },
    { dir: 'in', body: 'Full EP, 6 tracks. My name is Jamie by the way', ai: false },
    { dir: 'out', body: "Great to meet you, Jamie! For a 6-track EP we'd suggest a 5-day block. What's the best number to reach you for a quick scoping call?", ai: true },
  ];
  return (
    <div className="flex h-full">
      <div className="w-96 overflow-auto border-r border-[#2a2a3e]">
        {[
          { ch: 'SMS', unread: 2, preview: 'Full EP, 6 tracks. My name is Jamie…', active: true },
          { ch: 'SMS', unread: 0, preview: 'STOP', active: false },
          { ch: 'WEBCHAT', unread: 0, preview: 'What are your hours?', active: false },
        ].map((c, i) => (
          <button key={i} className={`w-full border-b border-[#2a2a3e]/60 px-4 py-3 text-left transition hover:bg-[#0f0f18] ${c.active ? 'bg-violet-500/10' : ''}`}>
            <p className="flex items-center justify-between text-sm font-medium text-white">
              <span className="flex items-center gap-2"><MessageSquare size={13} className="text-violet-400" />{c.ch}</span>
              {c.unread > 0 && <span className="rounded-full bg-violet-500 px-1.5 py-0.5 text-[10px] text-white">{c.unread}</span>}
            </p>
            <p className="mt-1 truncate text-xs text-gray-500">{c.preview}</p>
          </button>
        ))}
      </div>
      <div className="flex flex-1 flex-col">
        <div className="flex h-14 items-center justify-between border-b border-[#2a2a3e] px-5">
          <p className="text-sm text-gray-300">SMS conversation</p>
          <button className="flex items-center gap-1.5 rounded-lg border border-violet-500/60 bg-violet-500/10 px-3 py-1.5 text-xs text-[#c084fc]">
            <Bot size={14} /> AI On
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-auto p-5">
          {msgs.map((m, i) => (
            <div
              key={i}
              className={`max-w-[70%] rounded-xl px-4 py-2.5 text-sm ${
                m.dir === 'out'
                  ? 'ml-auto border border-violet-500/30 bg-violet-500/25 text-gray-100'
                  : 'border border-[#2a2a3e] bg-[#0f0f18] text-gray-200'
              }`}
            >
              <p>{m.body}</p>
              <p className="mt-1 flex items-center gap-1 text-[10px] text-gray-500">
                {m.ai && <Bot size={10} className="text-[#c084fc]" />} 2:4{i} PM
              </p>
            </div>
          ))}
        </div>
        <div className="flex gap-2 border-t border-[#2a2a3e] p-4">
          <input className={`${input} flex-1`} placeholder="Type a reply…" />
          <button className={btnPrimary}><Send size={16} /></button>
        </div>
      </div>
    </div>
  );
}

/* ================================ forms ================================= */

function Forms() {
  const [fields, setFields] = useState(FORM_FIELDS);
  const [copied, setCopied] = useState(false);
  const toggle = (key) =>
    setFields((f) => f.map((x) => (x.key === key ? { ...x, required: !x.required } : x)));
  return (
    <div className="flex h-full">
      <div className="flex w-80 flex-col border-r border-[#2a2a3e]">
        <div className="flex items-center justify-between border-b border-[#2a2a3e] p-4">
          <h2 className="text-sm font-semibold text-white">Lead Forms</h2>
          <button className={`${btnPrimary} px-2.5 py-1.5`}><Plus size={16} /></button>
        </div>
        <button className="border-b border-[#2a2a3e]/60 bg-violet-500/10 px-4 py-3 text-left">
          <p className="flex items-center justify-between text-sm font-medium text-white">
            Buyer leads
            <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400">Live</span>
          </p>
          <p className="mt-1 text-xs text-gray-500">38 submissions</p>
        </button>
        <button className="border-b border-[#2a2a3e]/60 px-4 py-3 text-left hover:bg-[#0f0f18]">
          <p className="flex items-center justify-between text-sm font-medium text-white">
            Studio booking
            <span className="rounded bg-gray-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-gray-400">Draft</span>
          </p>
          <p className="mt-1 text-xs text-gray-500">0 submissions</p>
        </button>
      </div>
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-3xl">
          <div className="flex items-center gap-3">
            <input className={`${input} flex-1 text-lg font-semibold`} defaultValue="Buyer leads" />
            <button className={`${btnGhost} flex items-center gap-1.5 !border-emerald-700 !text-emerald-400`}>
              <Globe size={15} /> Published
            </button>
            <button className={`${btnGhost} !border-rose-900/60 !text-rose-400 hover:!border-rose-500`}><Trash2 size={15} /></button>
          </div>
          <div className={`${card} mt-5 p-5`}>
            <p className={`${panelLabel} mb-4`}>Fields — drag to reorder</p>
            <div className="space-y-2">
              {fields.map((f) => (
                <div
                  key={f.key}
                  className={`flex items-center gap-3 rounded-lg border border-[#2a2a3e] bg-[#181826] px-3 py-2.5 ${
                    f.type === 'hidden' ? '' : ''
                  }`}
                >
                  <GripVertical size={16} className="cursor-grab text-gray-600 hover:text-gray-300" />
                  <div className="flex-1">
                    <p className="text-sm text-gray-200">{f.label}</p>
                    <p className="text-[11px] text-gray-500">
                      {f.type === 'hidden' ? 'hidden · workspace context' : f.type}
                    </p>
                  </div>
                  {f.type !== 'hidden' && (
                    <>
                      <button
                        onClick={() => toggle(f.key)}
                        className={`rounded border px-2 py-1 text-[11px] transition ${
                          f.required
                            ? 'border-violet-500/60 bg-violet-500/10 text-[#c084fc]'
                            : 'border-[#2a2a3e] text-gray-500'
                        }`}
                      >
                        Required
                      </button>
                      <Eye size={15} className="text-gray-500 hover:text-gray-300" />
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className={`${card} mt-4 p-5`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="flex items-center gap-2 text-sm font-medium text-white">
                  <Code2 size={15} className="text-violet-400" /> Embed on any site
                </p>
                <p className="mt-1 text-xs text-gray-500">Publish the form, then paste the iframe snippet into your landing page.</p>
              </div>
              <button
                className={`${btnPrimary} flex items-center gap-1.5`}
                onClick={() => { setCopied(true); setTimeout(() => setCopied(false), 2000); }}
              >
                {copied ? <Check size={15} /> : <Copy size={15} />}
                {copied ? 'Copied!' : 'Copy Embed Code'}
              </button>
            </div>
            <pre className="mt-4 overflow-x-auto whitespace-pre-wrap rounded-lg border border-[#2a2a3e] bg-[#08080d] p-3 text-xs text-[#c084fc]">
{`<iframe src="https://crm.example.com/api/v1/public/forms/9b2f…/render"
  width="100%" height="560"
  style="border:none;border-radius:12px;overflow:hidden"
  title="Buyer leads" loading="lazy"></iframe>`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ============================== automations ============================= */

function Automations() {
  const steps = [
    { icon: MessageSquare, label: 'SMS' },
    { icon: Mail, label: 'Email' },
    { icon: Clock, label: 'Wait 60s' },
    { icon: BellRing, label: 'Notify Owner' },
  ];
  return (
    <div className="max-w-5xl p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Automation Workflows</h2>
          <p className="mt-0.5 text-xs text-gray-500">Speed-to-lead sequences with A2P compliance guard and quiet-hours windows</p>
        </div>
        <button className={`${btnPrimary} flex items-center gap-1.5`}><Zap size={15} /> New Speed-to-Lead</button>
      </div>
      <div className={`${card} mt-5 p-5`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-white">Speed-to-Lead</p>
            <p className="mt-0.5 text-[11px] text-gray-500">Trigger: <span className="text-[#c084fc]">form_submission</span></p>
          </div>
          <div className="flex items-center gap-2">
            <button className="rounded-lg border border-emerald-700 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-400">Active</button>
            <Trash2 size={15} className="text-gray-600 hover:text-rose-400" />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          <span className="rounded border border-violet-500/30 bg-violet-500/15 px-2 py-1 text-[11px] text-[#c084fc]">Form Submission</span>
          {steps.map(({ icon: Icon, label }) => (
            <span key={label} className="flex items-center gap-1.5">
              <ChevronRight size={13} className="text-gray-600" />
              <span className="flex items-center gap-1.5 rounded border border-[#2a2a3e] bg-[#181826] px-2 py-1 text-[11px] text-gray-300">
                <Icon size={11} className="text-violet-400" />{label}
              </span>
            </span>
          ))}
        </div>
      </div>
      <div className={`${card} mt-8`}>
        <div className="border-b border-[#2a2a3e] px-5 py-4">
          <h3 className="text-sm font-semibold text-white">Execution Log</h3>
          <p className="mt-0.5 flex items-center gap-3 text-[11px] text-gray-500">
            <span className="flex items-center gap-1"><ShieldOff size={11} className="text-amber-400" /> compliance skips</span>
            <span className="flex items-center gap-1"><MoonStar size={11} className="text-indigo-400" /> quiet-hours pauses</span>
          </p>
        </div>
        <div className="max-h-96 overflow-auto">
          {EXEC_LOGS.map((log, i) => (
            <div key={i} className="flex items-center gap-3 border-b border-[#2a2a3e]/50 px-5 py-2.5">
              <span className={`rounded px-2 py-0.5 text-[10px] font-semibold ${STATE_STYLES[log.state]}`}>{log.state}</span>
              <span className="flex-1 truncate text-xs text-gray-400">{log.detail}</span>
              <span className="whitespace-nowrap text-[11px] text-gray-600">{log.at}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ============================= receptionist ============================= */

function Receptionist() {
  const [chat, setChat] = useState([
    { role: 'assistant', content: "Hi! I'm the Real Estate assistant — looking to buy, sell, or just exploring?" },
  ]);
  const [draft, setDraft] = useState('');
  const send = () => {
    if (!draft.trim()) return;
    setChat((c) => [
      ...c,
      { role: 'user', content: draft.trim() },
      { role: 'assistant', content: "Happy to help with that! What's the best name and number to reach you at so an agent can follow up?" },
    ]);
    setDraft('');
  };
  return (
    <div className="grid max-w-7xl grid-cols-1 gap-5 p-6 xl:grid-cols-3">
      <div className="space-y-5 xl:col-span-2">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
            <Bot size={18} className="text-violet-400" /> AI Receptionist
          </h2>
          <p className="mt-0.5 text-xs text-gray-500">
            An isolated persona for this workspace — it answers web chat and inbound SMS, and quietly turns conversations into contacts.
          </p>
        </div>
        <div className={`${card} space-y-4 p-5`}>
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-xs text-gray-400">Provider</label>
            <select className={input} defaultValue="anthropic">
              <option value="anthropic">Anthropic (Claude 3.5)</option>
              <option value="openai">OpenAI (fallback)</option>
              <option value="ollama">Ollama (local)</option>
            </select>
            <button className="flex items-center gap-1.5 rounded-lg border border-violet-500/60 bg-violet-500/10 px-2.5 py-1.5 text-[11px] text-[#c084fc]">
              <Globe2 size={13} /> Web Chat
            </button>
            <button className="flex items-center gap-1.5 rounded-lg border border-violet-500/60 bg-violet-500/10 px-2.5 py-1.5 text-[11px] text-[#c084fc]">
              <MessageSquare size={13} /> SMS
            </button>
          </div>
          <div>
            <label className="text-xs text-gray-400">Persona & business context (clean text only)</label>
            <textarea
              className={`${input} mt-1.5 h-32 w-full resize-y font-mono text-xs`}
              defaultValue={'# Horizon Realty\nBoutique agency serving the metro area.\n- Buyer representation\n- Listings & staging\n- Same-day showings'}
            />
          </div>
          <div className="border-t border-[#2a2a3e] pt-4">
            <label className="flex items-center gap-1.5 text-xs text-gray-400">
              <Sparkles size={13} className="text-violet-400" />
              Train from a URL or pasted page — HTML, scripts and CSS are stripped automatically
            </label>
            <div className="mt-1.5 flex gap-2">
              <input className={`${input} flex-1`} placeholder="https://your-business.com  — or paste raw page text" />
              <button className={btnPrimary}>Ingest</button>
            </div>
          </div>
        </div>
        <div className={card}>
          <div className="border-b border-[#2a2a3e] px-5 py-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-white">
              <UserCheck size={15} className="text-violet-400" /> Captured Sessions
            </h3>
          </div>
          <div className="px-5 py-3">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-300">Sarah Connor <span className="text-gray-500">· +1 (555) 123-4567</span></p>
              <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400">Contact created</span>
            </div>
            <p className="mt-1 truncate text-[11px] text-gray-600">Perfect — an agent will call you within the hour, Sarah!</p>
          </div>
        </div>
      </div>
      <div className={`${card} flex h-[36rem] flex-col`}>
        <div className="border-b border-[#2a2a3e] px-5 py-4">
          <h3 className="text-sm font-semibold text-white">Test the widget</h3>
          <p className="mt-0.5 text-[11px] text-gray-500">Talks to the same public endpoint external sites embed</p>
        </div>
        <div className="flex-1 space-y-2.5 overflow-auto p-4">
          {chat.map((m, i) => (
            <div
              key={i}
              className={`max-w-[85%] rounded-xl px-3.5 py-2 text-sm ${
                m.role === 'user'
                  ? 'ml-auto border border-violet-500/30 bg-violet-500/25 text-gray-100'
                  : 'border border-[#2a2a3e] bg-[#181826] text-gray-200'
              }`}
            >
              {m.content}
            </div>
          ))}
        </div>
        <div className="flex gap-2 border-t border-[#2a2a3e] p-3">
          <input
            className={`${input} flex-1`}
            placeholder="Say hi…"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <button className={btnPrimary} onClick={send}><Send size={15} /></button>
        </div>
      </div>
    </div>
  );
}

/* =============================== branding =============================== */

function Branding() {
  const [primary, setPrimary] = useState('#8B5CF6');
  const [accent, setAccent] = useState('#C084FC');
  const [name, setName] = useState('LeadStack');
  return (
    <div className="max-w-3xl space-y-5 p-6">
      <div>
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
          <Palette size={18} className="text-violet-400" /> White-Label Branding
        </h2>
        <p className="mt-0.5 text-xs text-gray-500">
          The entire platform identity — name, logos, colors — is driven by this configuration at runtime. Changes apply instantly, no redeploy.
        </p>
      </div>
      <div className={`${card} space-y-4 p-5`}>
        <p className="text-sm font-semibold text-white">Platform identity</p>
        <div className="grid grid-cols-2 gap-3">
          <label className="col-span-2 text-xs text-gray-400">
            Company name
            <input className={`${input} mt-1 w-full`} value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="text-xs text-gray-400">
            Primary color
            <span className="mt-1 flex items-center gap-2">
              <input type="color" className="h-9 w-9 cursor-pointer rounded border border-[#2a2a3e] bg-transparent" value={primary} onChange={(e) => setPrimary(e.target.value)} />
              <input className={`${input} flex-1`} value={primary} onChange={(e) => setPrimary(e.target.value)} />
            </span>
          </label>
          <label className="text-xs text-gray-400">
            Accent color
            <span className="mt-1 flex items-center gap-2">
              <input type="color" className="h-9 w-9 cursor-pointer rounded border border-[#2a2a3e] bg-transparent" value={accent} onChange={(e) => setAccent(e.target.value)} />
              <input className={`${input} flex-1`} value={accent} onChange={(e) => setAccent(e.target.value)} />
            </span>
          </label>
        </div>
        <div className="flex items-center justify-between rounded-lg border border-[#2a2a3e] p-4" style={{ background: '#0c0c13' }}>
          <p className="text-sm font-bold" style={{ color: primary }}>{name || 'Your platform'}</p>
          <button className="rounded-lg px-3 py-1.5 text-xs text-white" style={{ background: primary }}>Primary action</button>
          <span className="text-xs" style={{ color: accent }}>accent text</span>
        </div>
        <div className="flex justify-end">
          <button className={btnPrimary}>Save & apply</button>
        </div>
      </div>
      <div className={`${card} space-y-4 p-5`}>
        <p className="flex items-center gap-2 text-sm font-semibold text-white">
          <Building2 size={15} className="text-violet-400" /> Sender identity — Real Estate
        </p>
        <p className="-mt-2 text-xs text-gray-500">Outbound email and SMS for this workspace are sent under these values.</p>
        <div className="grid grid-cols-2 gap-3">
          {['From name', 'Reply-To email', 'SMS sender (Twilio number)', 'Owner email (internal alerts)'].map((l) => (
            <label key={l} className="text-xs text-gray-400">
              {l}
              <input className={`${input} mt-1 w-full`} placeholder={l.includes('Twilio') ? '+1…' : ''} />
            </label>
          ))}
        </div>
        <div className="flex justify-end">
          <button className={`${btnPrimary} flex items-center gap-1.5`}><Send size={14} /> Save sender identity</button>
        </div>
      </div>
    </div>
  );
}

/* =============================== landing ================================ */

function Landing() {
  const [open, setOpen] = useState(0);
  const faqs = [
    { q: 'Is my data really isolated between businesses?', a: 'Yes — isolation is enforced in the database layer, not just the UI. Every CRM row carries a workspace id and every query is filtered by it automatically.' },
    { q: 'How does SMS compliance work?', a: 'Inbound STOP, UNSUBSCRIBE, or QUIT instantly writes the number to an opt-out registry. Every outbound message checks it first and aborts with a logged SKIPPED_COMPLIANCE state on a hit.' },
    { q: 'Can I rebrand the whole platform?', a: 'Completely. Name, logos, colors and domain live in one configuration; the entire UI re-skins at runtime — no rebuild.' },
  ];
  const features = [
    { icon: KanbanSquare, t: 'Visual CRM Pipeline', b: 'Six stages, drag-and-drop Kanban, enforced lost reasons, real-time sync.' },
    { icon: MessageSquare, t: 'SMS Engine', b: 'Two-way Twilio texting with an opt-out registry that blocks sends early.' },
    { icon: FormInput, t: 'Embeddable Forms', b: 'Drag-to-order builder, one-tag iframe embed, leads routed per workspace.' },
    { icon: Zap, t: 'Speed-to-Lead', b: 'SMS + email within seconds of submission, owner alert a minute later.' },
    { icon: Bot, t: 'AI Receptionists', b: 'One persona per business, trained on your own site, capturing leads.' },
    { icon: ShieldCheck, t: 'Compliance Guard', b: 'STOP honored instantly; quiet hours respected per timezone.' },
    { icon: Users, t: 'Workspace Isolation', b: 'Row-level scoping makes cross-brand leaks impossible.' },
    { icon: Workflow, t: 'Automation Chains', b: 'Composable steps with full execution logs.' },
  ];
  return (
    <div className="min-h-screen bg-[#070710] text-gray-200">
      <header className="sticky top-0 z-40 border-b border-violet-900/30 bg-[#070710]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <p className="text-lg font-bold tracking-tight text-white"><span className="text-violet-400">Lead</span>Stack</p>
          <button className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white shadow-[0_0_24px_rgba(139,92,246,0.35)] transition hover:bg-violet-500">
            Open the app
          </button>
        </div>
      </header>
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0" style={{ background: 'radial-gradient(60% 50% at 50% 0%, rgba(139,92,246,0.22) 0%, rgba(7,7,16,0) 70%)' }} />
        <div className="relative mx-auto max-w-4xl px-6 pb-20 pt-24 text-center">
          <p className="inline-flex items-center gap-2 rounded-full border border-violet-700/50 bg-violet-500/10 px-4 py-1.5 text-xs uppercase tracking-[0.2em] text-violet-300">
            <Sparkles size={13} /> Your CRM. Your servers. Your rules.
          </p>
          <h1 className="mt-7 text-4xl font-extrabold leading-[1.08] tracking-tight text-white md:text-6xl">
            Stop renting your pipeline.
            <span className="block bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-transparent">Own the whole machine.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-400">
            One platform that runs every business you own — pipelines, lead-capture forms, speed-to-lead automation, and an AI receptionist for each brand.
          </p>
          <div className="mt-9 flex items-center justify-center gap-3">
            <button className="flex items-center gap-2 rounded-xl bg-violet-600 px-7 py-3.5 font-semibold text-white shadow-[0_0_36px_rgba(139,92,246,0.45)] transition hover:bg-violet-500">
              Launch your workspace <ArrowRight size={17} />
            </button>
            <button className="rounded-xl border border-violet-800/60 px-7 py-3.5 font-medium text-gray-300 transition hover:border-violet-500 hover:text-white">
              Calculate your savings
            </button>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map(({ icon: Icon, t, b }) => (
            <div key={t} className="rounded-2xl border border-violet-900/40 p-5 transition hover:border-violet-600/60 hover:bg-violet-500/[0.05]">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/15 text-violet-400"><Icon size={19} /></span>
              <h3 className="mt-4 text-sm font-semibold text-white">{t}</h3>
              <p className="mt-1.5 text-[13px] leading-relaxed text-gray-500">{b}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-3xl px-6 pb-20">
        <div className="space-y-3">
          {faqs.map((f, i) => (
            <div key={i} className={`overflow-hidden rounded-xl border transition-colors ${open === i ? 'border-violet-600/60 bg-violet-500/[0.05]' : 'border-violet-900/40'}`}>
              <button onClick={() => setOpen(open === i ? -1 : i)} className="flex w-full items-center justify-between px-5 py-4 text-left">
                <span className="text-sm font-medium text-gray-200">{f.q}</span>
                <ChevronDown size={17} className={`text-violet-400 transition-transform duration-300 ${open === i ? 'rotate-180' : ''}`} />
              </button>
              {open === i && <p className="px-5 pb-4 text-sm leading-relaxed text-gray-400">{f.a}</p>}
            </div>
          ))}
        </div>
        <div className="mt-16 text-center">
          <Rocket size={28} className="mx-auto text-violet-400" />
          <h2 className="mt-5 text-3xl font-extrabold tracking-tight text-white">Every month you wait is a SaaS invoice.</h2>
          <p className="mt-10 text-xs text-gray-600">© 2026 LeadStack — a self-owned CRM platform.</p>
        </div>
      </section>
    </div>
  );
}
