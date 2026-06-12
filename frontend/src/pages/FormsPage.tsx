import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  Plus, GripVertical, Copy, Check, Eye, EyeOff, Trash2, Code2, Globe,
} from 'lucide-react';
import { formsApi, LeadForm, FormField } from '../api/forms';

export function FormsPage() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: forms } = useQuery({
    queryKey: ['forms'],
    queryFn: () => formsApi.list(),
    select: (res) => res.data,
  });

  const createMutation = useMutation({
    mutationFn: () => formsApi.create({ name: 'Untitled form' }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['forms'] });
      setSelectedId(res.data.id);
    },
  });

  const selected = forms?.find((f) => f.id === selectedId) ?? null;

  return (
    <div className="flex h-full">
      {/* Form list */}
      <div className="w-80 border-r border-edge flex flex-col">
        <div className="p-4 border-b border-edge flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Lead Forms</h2>
          <button
            className="btn-primary px-2.5 py-1.5"
            onClick={() => createMutation.mutate()}
          >
            <Plus size={16} />
          </button>
        </div>
        <div className="flex-1 overflow-auto">
          {forms?.length === 0 && (
            <p className="p-4 text-sm text-gray-500">
              No forms yet. Create one to start capturing leads.
            </p>
          )}
          {forms?.map((f) => (
            <button
              key={f.id}
              onClick={() => setSelectedId(f.id)}
              className={`w-full text-left px-4 py-3 border-b border-edge/60 hover:bg-surface-raised transition ${
                selectedId === f.id ? 'bg-primary/10' : ''
              }`}
            >
              <p className="text-sm font-medium text-white flex items-center justify-between">
                {f.name}
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded ${
                    f.is_published
                      ? 'bg-emerald-500/15 text-emerald-400'
                      : 'bg-gray-500/15 text-gray-400'
                  }`}
                >
                  {f.is_published ? 'Live' : 'Draft'}
                </span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {f.submission_count} submissions
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Builder */}
      <div className="flex-1 overflow-auto">
        {!selected ? (
          <div className="h-full flex items-center justify-center text-gray-600 text-sm">
            Select a form to edit
          </div>
        ) : (
          <FormBuilder key={selected.id} form={selected} />
        )}
      </div>
    </div>
  );
}

function FormBuilder({ form }: { form: LeadForm }) {
  const [name, setName] = useState(form.name);
  const [fields, setFields] = useState<FormField[]>(form.fields_json);
  const [embed, setEmbed] = useState<{ snippet: string; url: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const queryClient = useQueryClient();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } })
  );

  const updateMutation = useMutation({
    mutationFn: (data: Partial<LeadForm>) => formsApi.update(form.id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['forms'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => formsApi.delete(form.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['forms'] }),
  });

  // Persist field layout changes (debounced)
  useEffect(() => {
    if (JSON.stringify(fields) === JSON.stringify(form.fields_json)) return;
    const t = setTimeout(() => updateMutation.mutate({ fields_json: fields }), 600);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fields]);

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setFields((prev) => {
      const oldIndex = prev.findIndex((f) => f.key === active.id);
      const newIndex = prev.findIndex((f) => f.key === over.id);
      return arrayMove(prev, oldIndex, newIndex);
    });
  };

  const patchField = (key: string, patch: Partial<FormField>) =>
    setFields((prev) => prev.map((f) => (f.key === key ? { ...f, ...patch } : f)));

  const copyEmbed = async () => {
    const res = await formsApi.embed(form.id);
    setEmbed({ snippet: res.data.snippet, url: res.data.embed_url });
    await navigator.clipboard.writeText(res.data.snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center justify-between gap-3">
        <input
          className="input text-lg font-semibold flex-1"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => name !== form.name && updateMutation.mutate({ name })}
        />
        <button
          className={`btn-ghost flex items-center gap-1.5 ${
            form.is_published ? 'border-emerald-700 text-emerald-400' : ''
          }`}
          onClick={() => updateMutation.mutate({ is_published: !form.is_published })}
        >
          <Globe size={15} />
          {form.is_published ? 'Published' : 'Publish'}
        </button>
        <button
          className="btn-ghost text-red-400 border-red-900/60 hover:border-red-500"
          onClick={() => deleteMutation.mutate()}
        >
          <Trash2 size={15} />
        </button>
      </div>

      <div className="card p-5 mt-5">
        <p className="text-[11px] uppercase tracking-wider text-gray-500 mb-4">
          Fields — drag to reorder
        </p>
        <DndContext sensors={sensors} onDragEnd={onDragEnd}>
          <SortableContext
            items={fields.map((f) => f.key)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2">
              {fields.map((field) => (
                <SortableFieldRow
                  key={field.key}
                  field={field}
                  onToggleRequired={() =>
                    patchField(field.key, { required: !field.required })
                  }
                  onToggleEnabled={() =>
                    patchField(field.key, { enabled: !field.enabled })
                  }
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      <div className="card p-5 mt-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white flex items-center gap-2">
              <Code2 size={15} className="text-primary" /> Embed on any site
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Publish the form, then paste the iframe snippet into your landing page.
            </p>
          </div>
          <button
            className="btn-primary flex items-center gap-1.5"
            disabled={!form.is_published}
            onClick={copyEmbed}
          >
            {copied ? <Check size={15} /> : <Copy size={15} />}
            {copied ? 'Copied!' : 'Copy Embed Code'}
          </button>
        </div>
        {embed && (
          <pre className="mt-4 bg-surface border border-edge rounded-lg p-3 text-xs text-accent overflow-x-auto whitespace-pre-wrap">
            {embed.snippet}
          </pre>
        )}
      </div>
    </div>
  );
}

function SortableFieldRow({
  field,
  onToggleRequired,
  onToggleEnabled,
}: {
  field: FormField;
  onToggleRequired: () => void;
  onToggleEnabled: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: field.key });

  const isContextField = field.key === 'sub_account_id';

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={`flex items-center gap-3 px-3 py-2.5 bg-surface-overlay border border-edge rounded-lg ${
        isDragging ? 'opacity-60 border-primary/70' : ''
      } ${!field.enabled ? 'opacity-50' : ''}`}
    >
      <button
        {...attributes}
        {...listeners}
        className="text-gray-600 hover:text-gray-300 cursor-grab active:cursor-grabbing"
      >
        <GripVertical size={16} />
      </button>
      <div className="flex-1">
        <p className="text-sm text-gray-200">{field.label}</p>
        <p className="text-[11px] text-gray-500">
          {isContextField ? 'hidden · workspace context' : field.type}
        </p>
      </div>
      {!isContextField && (
        <>
          <button
            onClick={onToggleRequired}
            className={`text-[11px] px-2 py-1 rounded border transition ${
              field.required
                ? 'border-primary/60 text-accent bg-primary/10'
                : 'border-edge text-gray-500'
            }`}
          >
            Required
          </button>
          <button
            onClick={onToggleEnabled}
            className="text-gray-500 hover:text-gray-300"
            title={field.enabled ? 'Disable field' : 'Enable field'}
          >
            {field.enabled ? <Eye size={15} /> : <EyeOff size={15} />}
          </button>
        </>
      )}
    </div>
  );
}
