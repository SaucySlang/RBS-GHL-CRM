import { useEffect, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bot, Globe2, MessageSquare, Sparkles, Send, UserCheck, Loader2,
} from 'lucide-react';
import { receptionistApi, ReceptionistConfig } from '../api/receptionist';
import { useSubAccountStore } from '../store/subAccountStore';

export function ReceptionistPage() {
  const queryClient = useQueryClient();

  const { data: config } = useQuery({
    queryKey: ['receptionist-config'],
    queryFn: () => receptionistApi.getConfig(),
    select: (res) => res.data,
  });

  const { data: sessions } = useQuery({
    queryKey: ['receptionist-sessions'],
    queryFn: () => receptionistApi.sessions(),
    select: (res) => res.data,
    refetchInterval: 8_000,
  });

  return (
    <div className="p-6 grid grid-cols-1 xl:grid-cols-3 gap-5 max-w-7xl">
      <div className="xl:col-span-2 space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Bot size={18} className="text-primary" /> AI Receptionist
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            An isolated persona for this workspace — it answers web chat and
            inbound SMS, and quietly turns conversations into contacts.
          </p>
        </div>

        {config && <ConfigEditor config={config} onSaved={() =>
          queryClient.invalidateQueries({ queryKey: ['receptionist-config'] })
        } />}

        <div className="card">
          <div className="px-5 py-4 border-b border-edge">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <UserCheck size={15} className="text-primary" /> Captured Sessions
            </h3>
          </div>
          <div className="max-h-72 overflow-auto">
            {sessions?.length === 0 && (
              <p className="p-4 text-sm text-gray-600">No chat sessions yet.</p>
            )}
            {sessions?.map((s) => (
              <div key={s.id} className="px-5 py-3 border-b border-edge/50">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-gray-300">
                    {s.extracted.name ?? 'Anonymous visitor'}
                    {s.extracted.phone && (
                      <span className="text-gray-500"> · {s.extracted.phone}</span>
                    )}
                  </p>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded ${
                      s.contact_id
                        ? 'bg-emerald-500/15 text-emerald-400'
                        : 'bg-gray-500/15 text-gray-400'
                    }`}
                  >
                    {s.contact_id ? 'Contact created' : 'Gathering info'}
                  </span>
                </div>
                <p className="text-[11px] text-gray-600 mt-1 truncate">
                  {s.transcript[s.transcript.length - 1]?.content ?? ''}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <TestChatPanel />
    </div>
  );
}

function ConfigEditor({
  config,
  onSaved,
}: {
  config: ReceptionistConfig;
  onSaved: () => void;
}) {
  const [context, setContext] = useState(config.prompt_context);
  const [trainSource, setTrainSource] = useState('');

  useEffect(() => setContext(config.prompt_context), [config.prompt_context]);

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ReceptionistConfig>) =>
      receptionistApi.updateConfig(data),
    onSuccess: onSaved,
  });

  const trainMutation = useMutation({
    mutationFn: () => receptionistApi.train(trainSource),
    onSuccess: () => {
      setTrainSource('');
      onSaved();
    },
  });

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <label className="text-xs text-gray-400">Provider</label>
        <select
          className="input"
          value={config.model_provider}
          onChange={(e) => updateMutation.mutate({ model_provider: e.target.value as ReceptionistConfig['model_provider'] })}
        >
          <option value="anthropic">Anthropic (Claude 3.5)</option>
          <option value="openai">OpenAI (fallback)</option>
          <option value="ollama">Ollama (local)</option>
        </select>
        <button
          className={`text-[11px] px-2.5 py-1.5 rounded-lg border flex items-center gap-1.5 transition ${
            config.web_chat_enabled
              ? 'border-primary/60 text-accent bg-primary/10'
              : 'border-edge text-gray-500'
          }`}
          onClick={() =>
            updateMutation.mutate({ web_chat_enabled: !config.web_chat_enabled })
          }
        >
          <Globe2 size={13} /> Web Chat
        </button>
        <button
          className={`text-[11px] px-2.5 py-1.5 rounded-lg border flex items-center gap-1.5 transition ${
            config.sms_enabled
              ? 'border-primary/60 text-accent bg-primary/10'
              : 'border-edge text-gray-500'
          }`}
          onClick={() => updateMutation.mutate({ sms_enabled: !config.sms_enabled })}
        >
          <MessageSquare size={13} /> SMS
        </button>
      </div>

      <div>
        <label className="text-xs text-gray-400">
          Persona & business context (clean text only)
        </label>
        <textarea
          className="input w-full h-40 mt-1.5 resize-y font-mono text-xs"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          onBlur={() =>
            context !== config.prompt_context &&
            updateMutation.mutate({ prompt_context: context })
          }
          placeholder="Describe the business, services, pricing, tone of voice…"
        />
      </div>

      <div className="border-t border-edge pt-4">
        <label className="text-xs text-gray-400 flex items-center gap-1.5">
          <Sparkles size={13} className="text-primary" />
          Train from a URL or pasted page — HTML, scripts and CSS are stripped
          automatically
        </label>
        <div className="flex gap-2 mt-1.5">
          <input
            className="input flex-1"
            placeholder="https://your-business.com  — or paste raw page text"
            value={trainSource}
            onChange={(e) => setTrainSource(e.target.value)}
          />
          <button
            className="btn-primary"
            disabled={!trainSource.trim() || trainMutation.isPending}
            onClick={() => trainMutation.mutate()}
          >
            {trainMutation.isPending ? <Loader2 size={15} className="animate-spin" /> : 'Ingest'}
          </button>
        </div>
      </div>
    </div>
  );
}

function TestChatPanel() {
  const activeSubAccountId = useSubAccountStore((s) => s.activeSubAccountId);
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const visitorKey = useRef(`test-${Math.random().toString(36).slice(2, 10)}`);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    if (!draft.trim() || !activeSubAccountId || busy) return;
    const text = draft.trim();
    setDraft('');
    setMessages((m) => [...m, { role: 'user', content: text }]);
    setBusy(true);
    try {
      const res = await receptionistApi.chat(activeSubAccountId, visitorKey.current, text);
      setMessages((m) => [...m, { role: 'assistant', content: res.data.reply }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: '(error — is the backend running?)' },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card flex flex-col h-[36rem]">
      <div className="px-5 py-4 border-b border-edge">
        <h3 className="text-sm font-semibold text-white">Test the widget</h3>
        <p className="text-[11px] text-gray-500 mt-0.5">
          Talks to the same public endpoint external sites embed
        </p>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-2.5">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-xl px-3.5 py-2 text-sm ${
              m.role === 'user'
                ? 'ml-auto bg-primary/25 border border-primary/30 text-gray-100'
                : 'bg-surface-overlay border border-edge text-gray-200'
            }`}
          >
            {m.content}
          </div>
        ))}
        {busy && (
          <div className="text-xs text-gray-500 flex items-center gap-1.5">
            <Loader2 size={12} className="animate-spin" /> thinking…
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-edge p-3 flex gap-2">
        <input
          className="input flex-1"
          placeholder="Say hi…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
        />
        <button className="btn-primary" onClick={send} disabled={busy || !draft.trim()}>
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}
