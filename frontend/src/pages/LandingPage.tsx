import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, Bot, Check, ChevronDown, CircleDollarSign, FormInput,
  KanbanSquare, MessageSquare, Rocket, ShieldCheck, Sparkles,
  Users, Workflow, X, Zap,
} from 'lucide-react';

export function LandingPage() {
  return (
    <div className="bg-[#070710] text-gray-200 min-h-screen">
      <TopBar />
      <Hero />
      <SixStepStrategy />
      <WorkspaceShowcase />
      <FeatureMatrix />
      <ComparisonTable />
      <RoiCalculator />
      <Faq />
      <FooterCta />
    </div>
  );
}

/* ---------------------------------- chrome --------------------------------- */

function TopBar() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-[#070710]/80 border-b border-violet-900/30">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <p className="font-bold text-lg tracking-tight text-white">
          <span className="text-violet-400">Lead</span>Stack
        </p>
        <nav className="hidden md:flex items-center gap-8 text-sm text-gray-400">
          <a href="#strategy" className="hover:text-white transition">Strategy</a>
          <a href="#features" className="hover:text-white transition">Features</a>
          <a href="#compare" className="hover:text-white transition">Compare</a>
          <a href="#roi" className="hover:text-white transition">ROI</a>
          <a href="#faq" className="hover:text-white transition">FAQ</a>
        </nav>
        <Link
          to="/pipeline"
          className="bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition shadow-[0_0_24px_rgba(139,92,246,0.35)]"
        >
          Open the app
        </Link>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(60% 50% at 50% 0%, rgba(139,92,246,0.22) 0%, rgba(7,7,16,0) 70%)',
        }}
      />
      <div className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center relative">
        <p className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-violet-300 border border-violet-700/50 rounded-full px-4 py-1.5 bg-violet-500/10">
          <Sparkles size={13} /> Your CRM. Your servers. Your rules.
        </p>
        <h1 className="mt-7 text-4xl md:text-6xl font-extrabold text-white leading-[1.08] tracking-tight">
          Stop renting your pipeline.
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-fuchsia-400">
            Own the whole machine.
          </span>
        </h1>
        <p className="mt-6 text-lg text-gray-400 max-w-2xl mx-auto">
          One platform that runs every business you own — pipelines, lead-capture
          forms, speed-to-lead automation, and an AI receptionist for each brand —
          with strict workspace isolation and zero per-seat ransom.
        </p>
        <div className="mt-9 flex items-center justify-center gap-3 flex-wrap">
          <Link
            to="/pipeline"
            className="bg-violet-600 hover:bg-violet-500 text-white font-semibold px-7 py-3.5 rounded-xl transition shadow-[0_0_36px_rgba(139,92,246,0.45)] flex items-center gap-2"
          >
            Launch your workspace <ArrowRight size={17} />
          </Link>
          <a
            href="#roi"
            className="border border-violet-800/60 hover:border-violet-500 text-gray-300 hover:text-white font-medium px-7 py-3.5 rounded-xl transition"
          >
            Calculate your savings
          </a>
        </div>
        <p className="mt-5 text-xs text-gray-600">
          Multi-tenant by design · A2P compliant out of the box · Runs on your stack
        </p>
      </div>
    </section>
  );
}

/* ------------------------------ 6-step strategy ----------------------------- */

const STEPS = [
  { n: '01', title: 'Spin up a workspace', body: 'One isolated sub-account per business — real estate, studio, store, consultancy. Data never crosses the wall.' },
  { n: '02', title: 'Drop a form on your page', body: 'Build it visually, copy one iframe tag, paste it on any landing page. Leads flow straight into the right workspace.' },
  { n: '03', title: 'Fire speed-to-lead', body: 'The instant a form lands: SMS in seconds, email right behind it, and you get pinged a minute later. No lead goes cold.' },
  { n: '04', title: 'Let the AI answer', body: 'A receptionist trained on your own site handles web chat and inbound texts, and quietly captures name + number.' },
  { n: '05', title: 'Work the board', body: 'Six stages from New Lead to Won. Drag, drop, and watch every tab stay in sync in real time.' },
  { n: '06', title: 'Collect the revenue', body: 'Lost deals demand a reason, won deals stack up, and the pipeline tells you exactly where the money is.' },
];

function SixStepStrategy() {
  return (
    <section id="strategy" className="max-w-6xl mx-auto px-6 py-20">
      <SectionHeading
        kicker="The 6-step strategy"
        title="From empty database to closed revenue"
        sub="A deliberate path — each step compounds the one before it."
      />
      <div className="grid md:grid-cols-3 gap-4 mt-12">
        {STEPS.map((s) => (
          <div
            key={s.n}
            className="border border-violet-900/40 rounded-2xl p-6 bg-gradient-to-b from-violet-500/[0.06] to-transparent hover:border-violet-600/60 transition group"
          >
            <p className="text-violet-500 font-mono text-sm group-hover:text-violet-300 transition">{s.n}</p>
            <h3 className="text-white font-semibold mt-3">{s.title}</h3>
            <p className="text-sm text-gray-500 mt-2 leading-relaxed">{s.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ----------------------------- workspace showcase --------------------------- */

function WorkspaceShowcase() {
  const deals = [
    { col: 'New Lead', items: [['Downtown duplex inquiry', '$8,400'], ['EP mixing — 6 tracks', '$2,200']] },
    { col: 'Qualified', items: [['Shopify migration', '$5,800']] },
    { col: 'Proposal Sent', items: [['AI chatbot rollout', '$12,000'], ['Listing: 1 4 Cedar Ln', '$9,750']] },
    { col: 'Won', items: [['Studio block — March', '$3,600']] },
  ];
  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <SectionHeading
        kicker="Inside a workspace"
        title="What a clean sub-account feels like"
        sub="Every business gets this view — its own pipeline, contacts, automations, and AI. Nothing bleeds between brands."
      />
      <div className="mt-12 border border-violet-900/50 rounded-2xl overflow-hidden shadow-[0_0_60px_rgba(139,92,246,0.15)]">
        {/* faux window chrome */}
        <div className="bg-[#0d0d18] border-b border-violet-900/40 px-5 py-3 flex items-center gap-3">
          <span className="flex gap-1.5">
            <i className="w-2.5 h-2.5 rounded-full bg-rose-500/70" />
            <i className="w-2.5 h-2.5 rounded-full bg-amber-500/70" />
            <i className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
          </span>
          <span className="text-xs text-gray-500 border border-violet-900/50 rounded-md px-2.5 py-1 flex items-center gap-1.5">
            <Users size={11} className="text-violet-400" /> Real Estate · workspace
          </span>
          <span className="text-[11px] text-gray-600 ml-auto hidden sm:block">
            live-synced across tabs
          </span>
        </div>
        <div className="bg-[#0a0a13] p-5 grid grid-cols-2 lg:grid-cols-4 gap-3">
          {deals.map((c) => (
            <div key={c.col} className="border border-violet-900/40 rounded-xl bg-[#0d0d18]">
              <p className="text-xs font-semibold text-violet-300 px-3.5 py-2.5 border-b border-violet-900/40">
                {c.col}
              </p>
              <div className="p-2.5 space-y-2">
                {c.items.map(([title, value]) => (
                  <div key={title} className="border border-violet-900/40 rounded-lg px-3 py-2.5 bg-[#11111d]">
                    <p className="text-[13px] text-gray-200 leading-snug">{title}</p>
                    <p className="text-xs text-violet-400 mt-1">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------- feature matrix ----------------------------- */

const FEATURES = [
  { icon: KanbanSquare, title: 'Visual CRM Pipeline', body: 'Six stages, drag-and-drop Kanban, enforced lost reasons, real-time sync.' },
  { icon: MessageSquare, title: 'SMS Engine', body: 'Two-way Twilio texting with an opt-out registry that blocks sends before carriers ever see them.' },
  { icon: FormInput, title: 'Embeddable Forms', body: 'Drag-to-order builder, one-tag iframe embed, leads mapped straight into the owning workspace.' },
  { icon: Zap, title: 'Speed-to-Lead', body: 'SMS + email within seconds of submission, owner alert a minute later. Automatic, every time.' },
  { icon: Bot, title: 'AI Receptionists', body: 'One persona per business, trained on your own site, capturing names and numbers in natural conversation.' },
  { icon: ShieldCheck, title: 'Compliance Guard', body: 'STOP keywords honored instantly; quiet hours respected per timezone, per workspace.' },
  { icon: Users, title: 'Workspace Isolation', body: 'Agency → sub-account → member. Row-level scoping makes cross-brand leaks impossible.' },
  { icon: Workflow, title: 'Automation Chains', body: 'Composable steps with full execution logs — including why something was skipped or paused.' },
];

function FeatureMatrix() {
  return (
    <section id="features" className="max-w-6xl mx-auto px-6 py-20">
      <SectionHeading
        kicker="Feature matrix"
        title="Everything native. Nothing bolted on."
        sub="No marketplace add-ons, no per-feature upsells — the whole stack ships together."
      />
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-12">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <div
            key={title}
            className="border border-violet-900/40 rounded-2xl p-5 hover:bg-violet-500/[0.05] hover:border-violet-600/60 transition"
          >
            <span className="w-10 h-10 rounded-xl bg-violet-500/15 text-violet-400 flex items-center justify-center">
              <Icon size={19} />
            </span>
            <h3 className="text-white text-sm font-semibold mt-4">{title}</h3>
            <p className="text-[13px] text-gray-500 mt-1.5 leading-relaxed">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ------------------------------ comparison table ---------------------------- */

type Cell = boolean | string;
const COMPARISON: { label: string; ls: Cell; ghl: Cell; hs: Cell }[] = [
  { label: 'Monthly platform fee', ls: 'Your hosting bill', ghl: '$97–$497/mo', hs: '$800+/mo (Pro)' },
  { label: 'Unlimited sub-accounts', ls: true, ghl: '$297/mo tier', hs: false },
  { label: 'Per-seat pricing', ls: 'Never', ghl: 'On some plans', hs: '$45+/seat' },
  { label: 'Own your data & code', ls: true, ghl: false, hs: false },
  { label: 'AI receptionist per brand', ls: true, ghl: 'Paid add-on', hs: 'Paid add-on' },
  { label: 'A2P opt-out registry built in', ls: true, ghl: true, hs: 'Partial' },
  { label: 'Embeddable form builder', ls: true, ghl: true, hs: true },
  { label: 'Real-time Kanban sync', ls: true, ghl: true, hs: true },
  { label: 'White-label re-skin in minutes', ls: true, ghl: '$497/mo tier', hs: false },
];

function CellValue({ value }: { value: Cell }) {
  if (value === true) return <Check size={16} className="text-emerald-400 mx-auto" />;
  if (value === false) return <X size={16} className="text-rose-500/80 mx-auto" />;
  return <span className="text-xs text-gray-400">{value}</span>;
}

function ComparisonTable() {
  return (
    <section id="compare" className="max-w-5xl mx-auto px-6 py-20">
      <SectionHeading
        kicker="Head to head"
        title="The honest comparison"
        sub="Feature for feature against the platforms you'd otherwise be paying forever."
      />
      <div className="mt-12 border border-violet-900/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-violet-500/[0.07] text-left">
              <th className="px-5 py-4 text-gray-400 font-medium w-2/5"> </th>
              <th className="px-4 py-4 text-center">
                <span className="text-violet-300 font-bold">LeadStack</span>
                <span className="block text-[10px] text-violet-500 font-normal mt-0.5">self-owned</span>
              </th>
              <th className="px-4 py-4 text-center text-gray-300 font-semibold">GoHighLevel</th>
              <th className="px-4 py-4 text-center text-gray-300 font-semibold">HubSpot</th>
            </tr>
          </thead>
          <tbody>
            {COMPARISON.map((row, i) => (
              <tr
                key={row.label}
                className={`border-t border-violet-900/30 ${i % 2 ? 'bg-white/[0.015]' : ''}`}
              >
                <td className="px-5 py-3.5 text-gray-300">{row.label}</td>
                <td className="px-4 py-3.5 text-center bg-violet-500/[0.05]"><CellValue value={row.ls} /></td>
                <td className="px-4 py-3.5 text-center"><CellValue value={row.ghl} /></td>
                <td className="px-4 py-3.5 text-center"><CellValue value={row.hs} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-gray-600 mt-3">
        Published list pricing, late 2025. Check vendors for current rates.
      </p>
    </section>
  );
}

/* -------------------------------- ROI calculator ---------------------------- */

function RoiCalculator() {
  const [businesses, setBusinesses] = useState(3);
  const [seats, setSeats] = useState(4);
  const [perAppCost, setPerAppCost] = useState(180);

  const monthlySaas = useMemo(() => {
    // What the same footprint costs on rented platforms:
    // a sub-account-tier platform fee + per-seat CRM + the misc app stack
    const platformFee = businesses > 1 ? 297 : 97;
    const seatFees = seats * 45;
    return platformFee + seatFees + perAppCost;
  }, [businesses, seats, perAppCost]);

  const selfHosted = 40; // typical VPS + Postgres
  const monthlySavings = Math.max(0, monthlySaas - selfHosted);
  const yearlySavings = monthlySavings * 12;

  return (
    <section id="roi" className="max-w-4xl mx-auto px-6 py-20">
      <SectionHeading
        kicker="ROI calculator"
        title="What does renting actually cost you?"
        sub="Slide to match your setup. We compare a typical SaaS stack against running this platform yourself."
      />
      <div className="mt-12 border border-violet-900/50 rounded-2xl p-7 bg-gradient-to-b from-violet-500/[0.06] to-transparent">
        <div className="space-y-7">
          <Slider
            label="Businesses you run"
            value={businesses}
            min={1} max={10}
            display={`${businesses}`}
            onChange={setBusinesses}
          />
          <Slider
            label="Team seats"
            value={seats}
            min={1} max={25}
            display={`${seats}`}
            onChange={setSeats}
          />
          <Slider
            label="Other tools you'd replace (forms, chat, SMS, scheduler)"
            value={perAppCost}
            min={0} max={600} step={20}
            display={`$${perAppCost}/mo`}
            onChange={setPerAppCost}
          />
        </div>

        <div className="grid sm:grid-cols-3 gap-4 mt-9">
          <RoiStat label="Typical SaaS stack" value={`$${monthlySaas.toLocaleString()}/mo`} tone="dim" />
          <RoiStat label="Self-owned platform" value={`~$${selfHosted}/mo`} tone="dim" />
          <RoiStat label="You keep" value={`$${yearlySavings.toLocaleString()}/yr`} tone="hot" />
        </div>
      </div>
    </section>
  );
}

function Slider({
  label, value, min, max, step = 1, display, onChange,
}: {
  label: string; value: number; min: number; max: number; step?: number;
  display: string; onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2.5">
        <label className="text-sm text-gray-400">{label}</label>
        <span className="text-sm font-semibold text-violet-300">{display}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-violet-500 cursor-pointer"
      />
    </div>
  );
}

function RoiStat({ label, value, tone }: { label: string; value: string; tone: 'dim' | 'hot' }) {
  return (
    <div
      className={`rounded-xl border p-5 text-center ${
        tone === 'hot'
          ? 'border-violet-500/60 bg-violet-500/10 shadow-[0_0_30px_rgba(139,92,246,0.25)]'
          : 'border-violet-900/40'
      }`}
    >
      <p className="text-[11px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className={`mt-1.5 text-2xl font-bold ${tone === 'hot' ? 'text-violet-300' : 'text-gray-200'}`}>
        {value}
      </p>
    </div>
  );
}

/* ------------------------------------ FAQ ----------------------------------- */

const FAQS = [
  {
    q: 'Is my data really isolated between businesses?',
    a: 'Yes — isolation is enforced in the database layer, not just the UI. Every CRM row carries a workspace id and every query is filtered by it automatically, so one brand can never see another\'s contacts, deals, or conversations.',
  },
  {
    q: 'How does SMS compliance work?',
    a: 'Inbound STOP, UNSUBSCRIBE, or QUIT instantly writes the number to an opt-out registry. Every outbound message — manual or automated — checks that registry first and aborts with a logged SKIPPED_COMPLIANCE state if there\'s a hit. Quiet hours are honored per workspace timezone.',
  },
  {
    q: 'Which AI models power the receptionist?',
    a: 'Anthropic Claude 3.5 by default, with automatic fallback to OpenAI and then a local Ollama instance if configured. Each workspace picks its own provider and persona.',
  },
  {
    q: 'Can I embed forms on pages I host elsewhere?',
    a: 'Yes. Publish a form, copy the iframe snippet, and paste it into any landing page. The embed endpoint explicitly allows cross-origin framing and submissions are mapped to the workspace that owns the form.',
  },
  {
    q: 'Can I rebrand the whole platform?',
    a: 'Completely. Company name, logos, primary and accent colors, and the custom domain live in one configuration. Change them in the admin dashboard and the entire UI re-skins at runtime — no rebuild.',
  },
  {
    q: 'What do I need to run it?',
    a: 'A Postgres database and a small server for the FastAPI backend + React frontend. Twilio and SendGrid keys enable SMS and email; AI keys enable the receptionist. Everything degrades gracefully without them.',
  },
];

function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section id="faq" className="max-w-3xl mx-auto px-6 py-20">
      <SectionHeading
        kicker="FAQ"
        title="Asked and answered"
        sub=""
      />
      <div className="mt-10 space-y-3">
        {FAQS.map((item, i) => {
          const isOpen = open === i;
          return (
            <div
              key={item.q}
              className={`border rounded-xl overflow-hidden transition-colors ${
                isOpen ? 'border-violet-600/60 bg-violet-500/[0.05]' : 'border-violet-900/40'
              }`}
            >
              <button
                onClick={() => setOpen(isOpen ? null : i)}
                className="w-full flex items-center justify-between px-5 py-4 text-left"
              >
                <span className="text-sm font-medium text-gray-200">{item.q}</span>
                <ChevronDown
                  size={17}
                  className={`text-violet-400 transition-transform duration-300 ${
                    isOpen ? 'rotate-180' : ''
                  }`}
                />
              </button>
              <div
                className={`grid transition-all duration-300 ease-in-out ${
                  isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
                }`}
              >
                <div className="overflow-hidden">
                  <p className="px-5 pb-4 text-sm text-gray-400 leading-relaxed">{item.a}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* --------------------------------- footer CTA ------------------------------- */

function FooterCta() {
  return (
    <section className="relative overflow-hidden border-t border-violet-900/30">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(50% 60% at 50% 100%, rgba(139,92,246,0.18) 0%, rgba(7,7,16,0) 70%)',
        }}
      />
      <div className="max-w-3xl mx-auto px-6 py-24 text-center relative">
        <Rocket size={28} className="text-violet-400 mx-auto" />
        <h2 className="mt-5 text-3xl md:text-4xl font-extrabold text-white tracking-tight">
          Every month you wait is a SaaS invoice.
        </h2>
        <p className="mt-4 text-gray-400">
          Your businesses, your pipelines, your AI — under one roof you own.
        </p>
        <Link
          to="/pipeline"
          className="inline-flex items-center gap-2 mt-8 bg-violet-600 hover:bg-violet-500 text-white font-semibold px-8 py-4 rounded-xl transition shadow-[0_0_40px_rgba(139,92,246,0.45)]"
        >
          <CircleDollarSign size={18} /> Start running on your own stack
        </Link>
        <p className="mt-10 text-xs text-gray-600">
          © {new Date().getFullYear()} LeadStack — a self-owned CRM platform.
        </p>
      </div>
    </section>
  );
}

/* --------------------------------- shared bits ------------------------------ */

function SectionHeading({ kicker, title, sub }: { kicker: string; title: string; sub: string }) {
  return (
    <div className="text-center max-w-2xl mx-auto">
      <p className="text-xs uppercase tracking-[0.25em] text-violet-400">{kicker}</p>
      <h2 className="mt-3 text-3xl md:text-4xl font-extrabold text-white tracking-tight">
        {title}
      </h2>
      {sub && <p className="mt-3 text-gray-500">{sub}</p>}
    </div>
  );
}
