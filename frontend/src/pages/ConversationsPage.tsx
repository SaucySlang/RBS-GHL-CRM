import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bot, Send, MessageSquare } from 'lucide-react';
import { conversationsApi, messagesApi, Conversation } from '../api/client';

export function ConversationsPage() {
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [draft, setDraft] = useState('');
  const queryClient = useQueryClient();

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationsApi.list('open'),
    select: (res) => res.data,
    refetchInterval: 10_000,
  });

  const { data: messages } = useQuery({
    queryKey: ['conversation-messages', selected?.id],
    queryFn: () => conversationsApi.messages(selected!.id),
    select: (res) => res.data,
    enabled: !!selected,
    refetchInterval: 5_000,
  });

  const sendMutation = useMutation({
    mutationFn: () =>
      messagesApi.send({
        contact_id: selected!.contact_id,
        channel: selected!.channel,
        body: draft.trim(),
      }),
    onSuccess: () => {
      setDraft('');
      queryClient.invalidateQueries({ queryKey: ['conversation-messages', selected?.id] });
    },
  });

  const toggleAiMutation = useMutation({
    mutationFn: (enabled: boolean) => conversationsApi.toggleAi(selected!.id, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['conversations'] }),
  });

  return (
    <div className="flex h-full">
      {/* Conversation list */}
      <div className="w-96 border-r border-edge overflow-auto">
        {conversations?.length === 0 && (
          <p className="p-4 text-sm text-gray-500">No open conversations.</p>
        )}
        {conversations?.map((c) => (
          <button
            key={c.id}
            onClick={() => setSelected(c)}
            className={`w-full text-left px-4 py-3 border-b border-edge/60 hover:bg-surface-raised transition ${
              selected?.id === c.id ? 'bg-primary/10' : ''
            }`}
          >
            <p className="text-sm font-medium text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <MessageSquare size={13} className="text-primary" />
                {c.channel.toUpperCase()}
              </span>
              {c.unread_count > 0 && (
                <span className="text-[10px] bg-primary text-white rounded-full px-1.5 py-0.5">
                  {c.unread_count}
                </span>
              )}
            </p>
            <p className="text-xs text-gray-500 mt-1 truncate">
              {c.last_message_preview ?? 'No messages yet'}
            </p>
          </button>
        ))}
      </div>

      {/* Thread */}
      <div className="flex-1 flex flex-col">
        {!selected ? (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
            Select a conversation
          </div>
        ) : (
          <>
            <div className="h-14 border-b border-edge flex items-center justify-between px-5">
              <p className="text-sm text-gray-300">
                {selected.channel.toUpperCase()} conversation
              </p>
              <button
                onClick={() => toggleAiMutation.mutate(!selected.ai_enabled)}
                className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition ${
                  selected.ai_enabled
                    ? 'border-primary/60 text-accent bg-primary/10'
                    : 'border-edge text-gray-500'
                }`}
              >
                <Bot size={14} />
                AI {selected.ai_enabled ? 'On' : 'Off'}
              </button>
            </div>
            <div className="flex-1 overflow-auto p-5 space-y-3">
              {messages?.map((m) => (
                <div
                  key={m.id}
                  className={`max-w-[70%] rounded-xl px-4 py-2.5 text-sm ${
                    m.direction === 'outbound'
                      ? 'ml-auto bg-primary/25 text-gray-100 border border-primary/30'
                      : 'bg-surface-raised border border-edge text-gray-200'
                  }`}
                >
                  <p>{m.body}</p>
                  <p className="text-[10px] text-gray-500 mt-1 flex items-center gap-1">
                    {m.ai_generated && <Bot size={10} className="text-accent" />}
                    {new Date(m.created_at).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
            <div className="border-t border-edge p-4 flex gap-2">
              <input
                className="input flex-1"
                placeholder="Type a reply…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && draft.trim()) sendMutation.mutate();
                }}
              />
              <button
                className="btn-primary"
                disabled={!draft.trim() || sendMutation.isPending}
                onClick={() => sendMutation.mutate()}
              >
                <Send size={16} />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
