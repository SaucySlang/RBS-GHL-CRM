import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Plus, Phone, Mail, Ban, Trash2, StickyNote, X } from 'lucide-react';
import { contactsApi, Contact } from '../api/client';

function displayName(c: Contact) {
  const name = [c.first_name, c.last_name].filter(Boolean).join(' ');
  return name || c.email || c.phone || 'Unnamed contact';
}

export function ContactsPage() {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Contact | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [noteBody, setNoteBody] = useState('');
  const queryClient = useQueryClient();

  const { data: contacts, isLoading } = useQuery({
    queryKey: ['contacts', search],
    queryFn: () => contactsApi.list({ search: search || undefined }),
    select: (res) => res.data,
  });

  const { data: notes } = useQuery({
    queryKey: ['contact-notes', selected?.id],
    queryFn: () => contactsApi.notes(selected!.id),
    select: (res) => res.data,
    enabled: !!selected,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => contactsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setSelected(null);
    },
  });

  const addNoteMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: string }) =>
      contactsApi.addNote(id, body),
    onSuccess: () => {
      setNoteBody('');
      queryClient.invalidateQueries({ queryKey: ['contact-notes', selected?.id] });
    },
  });

  return (
    <div className="flex h-full">
      {/* Contact list */}
      <div className="w-96 border-r border-edge flex flex-col">
        <div className="p-4 border-b border-edge flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-2.5 text-gray-500" size={17} />
            <input
              type="text"
              placeholder="Search contacts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input w-full pl-10"
            />
          </div>
          <button onClick={() => setShowCreate(true)} className="btn-primary px-2.5">
            <Plus size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-auto">
          {isLoading && <p className="p-4 text-sm text-gray-500">Loading…</p>}
          {contacts?.length === 0 && (
            <p className="p-4 text-sm text-gray-500">No contacts in this workspace yet.</p>
          )}
          {contacts?.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelected(c)}
              className={`w-full text-left px-4 py-3 border-b border-edge/60 hover:bg-surface-raised transition ${
                selected?.id === c.id ? 'bg-primary/10' : ''
              }`}
            >
              <p className="text-sm font-medium text-white flex items-center gap-2">
                {displayName(c)}
                {c.do_not_disturb && <Ban size={13} className="text-red-400" />}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">
                {c.email || c.phone || '—'}
              </p>
              {c.tags.length > 0 && (
                <span className="inline-flex gap-1 mt-1.5 flex-wrap">
                  {c.tags.map((t) => (
                    <span
                      key={t}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-primary/15 text-accent"
                    >
                      {t}
                    </span>
                  ))}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div className="flex-1 overflow-auto">
        {!selected ? (
          <div className="h-full flex items-center justify-center text-gray-600 text-sm">
            Select a contact to view details
          </div>
        ) : (
          <div className="p-6 max-w-2xl">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">{displayName(selected)}</h2>
                <p className="text-xs text-gray-500 mt-1">
                  Source: {selected.source ?? 'manual'} · Created{' '}
                  {new Date(selected.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(selected.id)}
                className="btn-ghost text-red-400 border-red-900/60 hover:border-red-500"
              >
                <Trash2 size={15} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mt-6">
              <div className="card p-4">
                <p className="text-[11px] uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                  <Phone size={12} /> Phone
                </p>
                <p className="text-sm text-gray-200 mt-1">{selected.phone ?? '—'}</p>
              </div>
              <div className="card p-4">
                <p className="text-[11px] uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                  <Mail size={12} /> Email
                </p>
                <p className="text-sm text-gray-200 mt-1">{selected.email ?? '—'}</p>
              </div>
            </div>

            <div className="card p-4 mt-4">
              <p className="text-[11px] uppercase tracking-wider text-gray-500 flex items-center gap-1.5 mb-3">
                <StickyNote size={12} /> Notes
              </p>
              <div className="flex gap-2 mb-3">
                <input
                  className="input flex-1"
                  placeholder="Add a note…"
                  value={noteBody}
                  onChange={(e) => setNoteBody(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && noteBody.trim()) {
                      addNoteMutation.mutate({ id: selected.id, body: noteBody.trim() });
                    }
                  }}
                />
                <button
                  className="btn-primary"
                  disabled={!noteBody.trim()}
                  onClick={() =>
                    addNoteMutation.mutate({ id: selected.id, body: noteBody.trim() })
                  }
                >
                  Add
                </button>
              </div>
              {notes?.map((n) => (
                <div key={n.id} className="border-t border-edge/60 py-2.5">
                  <p className="text-sm text-gray-300">{n.body}</p>
                  <p className="text-[11px] text-gray-600 mt-1">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>
              ))}
              {notes?.length === 0 && (
                <p className="text-xs text-gray-600">No notes yet.</p>
              )}
            </div>
          </div>
        )}
      </div>

      {showCreate && <CreateContactModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function CreateContactModal({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '' });
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: () =>
      contactsApi.create({
        first_name: form.first_name || null,
        last_name: form.last_name || null,
        email: form.email || null,
        phone: form.phone || null,
      } as Partial<Contact>),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="card bg-surface-overlay p-6 w-[420px]">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-base font-semibold text-white">New Contact</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <input
            className="input"
            placeholder="First name"
            value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
          />
          <input
            className="input"
            placeholder="Last name"
            value={form.last_name}
            onChange={(e) => setForm({ ...form, last_name: e.target.value })}
          />
          <input
            className="input col-span-2"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            className="input col-span-2"
            placeholder="Phone"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="btn-ghost">
            Cancel
          </button>
          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="btn-primary"
          >
            Create
          </button>
        </div>
      </div>
    </div>
  );
}
