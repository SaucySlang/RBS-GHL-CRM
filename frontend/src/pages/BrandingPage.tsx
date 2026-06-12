import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Palette, Save, Building2, Send } from 'lucide-react';
import { api } from '../api/client';
import { Branding } from '../theme/ThemeProvider';
import { useSubAccountStore, SubAccount } from '../store/subAccountStore';
import { subAccountsApi } from '../api/client';

interface BrandingRow extends Branding {
  id: string;
  updated_at: string;
}

export function BrandingPage() {
  const queryClient = useQueryClient();

  const { data: branding } = useQuery({
    queryKey: ['branding-admin'],
    queryFn: () => api.get<BrandingRow>('/branding/'),
    select: (res) => res.data,
  });

  return (
    <div className="p-6 max-w-3xl space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Palette size={18} className="text-primary" /> White-Label Branding
        </h2>
        <p className="text-xs text-gray-500 mt-0.5">
          The entire platform identity — name, logos, colors — is driven by this
          configuration at runtime. Changes apply instantly, no redeploy.
        </p>
      </div>

      {branding && (
        <PlatformBrandingCard
          branding={branding}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ['branding-admin'] });
            queryClient.invalidateQueries({ queryKey: ['branding'] });
          }}
        />
      )}

      <SenderIdentityCard />
    </div>
  );
}

function PlatformBrandingCard({
  branding,
  onSaved,
}: {
  branding: BrandingRow;
  onSaved: () => void;
}) {
  const [form, setForm] = useState({
    company_name: branding.company_name,
    logo_dark_url: branding.logo_dark_url ?? '',
    logo_light_url: branding.logo_light_url ?? '',
    primary_color: branding.primary_color,
    accent_color: branding.accent_color,
    custom_domain: branding.custom_domain ?? '',
  });

  useEffect(() => {
    setForm({
      company_name: branding.company_name,
      logo_dark_url: branding.logo_dark_url ?? '',
      logo_light_url: branding.logo_light_url ?? '',
      primary_color: branding.primary_color,
      accent_color: branding.accent_color,
      custom_domain: branding.custom_domain ?? '',
    });
  }, [branding]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api.patch('/branding/', {
        ...form,
        logo_dark_url: form.logo_dark_url || null,
        logo_light_url: form.logo_light_url || null,
        custom_domain: form.custom_domain || null,
      }),
    onSuccess: onSaved,
  });

  return (
    <div className="card p-5 space-y-4">
      <p className="text-sm font-semibold text-white">Platform identity</p>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-xs text-gray-400 col-span-2">
          Company name
          <input
            className="input w-full mt-1"
            value={form.company_name}
            onChange={(e) => setForm({ ...form, company_name: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          Logo URL (dark surfaces)
          <input
            className="input w-full mt-1"
            value={form.logo_dark_url}
            onChange={(e) => setForm({ ...form, logo_dark_url: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          Logo URL (light surfaces / emails)
          <input
            className="input w-full mt-1"
            value={form.logo_light_url}
            onChange={(e) => setForm({ ...form, logo_light_url: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          Primary color
          <span className="flex items-center gap-2 mt-1">
            <input
              type="color"
              className="w-9 h-9 rounded border border-edge bg-transparent cursor-pointer"
              value={form.primary_color}
              onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
            />
            <input
              className="input flex-1"
              value={form.primary_color}
              onChange={(e) => setForm({ ...form, primary_color: e.target.value })}
            />
          </span>
        </label>
        <label className="text-xs text-gray-400">
          Accent color
          <span className="flex items-center gap-2 mt-1">
            <input
              type="color"
              className="w-9 h-9 rounded border border-edge bg-transparent cursor-pointer"
              value={form.accent_color}
              onChange={(e) => setForm({ ...form, accent_color: e.target.value })}
            />
            <input
              className="input flex-1"
              value={form.accent_color}
              onChange={(e) => setForm({ ...form, accent_color: e.target.value })}
            />
          </span>
        </label>
        <label className="text-xs text-gray-400 col-span-2">
          Custom domain
          <input
            className="input w-full mt-1"
            placeholder="crm.yourbrand.com"
            value={form.custom_domain}
            onChange={(e) => setForm({ ...form, custom_domain: e.target.value })}
          />
        </label>
      </div>

      {/* Live preview strip */}
      <div
        className="rounded-lg border border-edge p-4 flex items-center justify-between"
        style={{ background: '#0c0c13' }}
      >
        <p className="text-sm font-bold" style={{ color: form.primary_color }}>
          {form.company_name || 'Your platform'}
        </p>
        <button
          className="text-xs text-white px-3 py-1.5 rounded-lg"
          style={{ background: form.primary_color }}
        >
          Primary action
        </button>
        <span className="text-xs" style={{ color: form.accent_color }}>
          accent text
        </span>
      </div>

      <div className="flex justify-end">
        <button
          className="btn-primary flex items-center gap-1.5"
          disabled={saveMutation.isPending}
          onClick={() => saveMutation.mutate()}
        >
          <Save size={15} /> Save & apply
        </button>
      </div>
    </div>
  );
}

function SenderIdentityCard() {
  const queryClient = useQueryClient();
  const activeSubAccountId = useSubAccountStore((s) => s.activeSubAccountId);
  const subAccounts = useSubAccountStore((s) => s.subAccounts);
  const active = subAccounts.find((s) => s.id === activeSubAccountId);

  const [form, setForm] = useState({
    from_name: '',
    reply_to_email: '',
    twilio_phone_number: '',
    owner_email: '',
    owner_phone: '',
  });

  useEffect(() => {
    if (active) {
      setForm({
        from_name: active.from_name ?? '',
        reply_to_email: active.reply_to_email ?? '',
        twilio_phone_number: active.twilio_phone_number ?? '',
        owner_email: active.owner_email ?? '',
        owner_phone: active.owner_phone ?? '',
      });
    }
  }, [active?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const saveMutation = useMutation({
    mutationFn: () =>
      subAccountsApi.update(activeSubAccountId!, {
        from_name: form.from_name || null,
        reply_to_email: form.reply_to_email || null,
        twilio_phone_number: form.twilio_phone_number || null,
        owner_email: form.owner_email || null,
        owner_phone: form.owner_phone || null,
      } as Partial<SubAccount>),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sub-accounts'] }),
  });

  if (!active) return null;

  return (
    <div className="card p-5 space-y-4">
      <p className="text-sm font-semibold text-white flex items-center gap-2">
        <Building2 size={15} className="text-primary" />
        Sender identity — {active.name}
      </p>
      <p className="text-xs text-gray-500 -mt-2">
        Outbound email and SMS for this workspace are sent under these values.
      </p>
      <div className="grid grid-cols-2 gap-3">
        <label className="text-xs text-gray-400">
          From name
          <input
            className="input w-full mt-1"
            value={form.from_name}
            onChange={(e) => setForm({ ...form, from_name: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          Reply-To email
          <input
            className="input w-full mt-1"
            value={form.reply_to_email}
            onChange={(e) => setForm({ ...form, reply_to_email: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          SMS sender (Twilio number)
          <input
            className="input w-full mt-1"
            placeholder="+1…"
            value={form.twilio_phone_number}
            onChange={(e) => setForm({ ...form, twilio_phone_number: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          Owner email (internal alerts)
          <input
            className="input w-full mt-1"
            value={form.owner_email}
            onChange={(e) => setForm({ ...form, owner_email: e.target.value })}
          />
        </label>
        <label className="text-xs text-gray-400">
          Owner phone (internal alerts)
          <input
            className="input w-full mt-1"
            value={form.owner_phone}
            onChange={(e) => setForm({ ...form, owner_phone: e.target.value })}
          />
        </label>
      </div>
      <div className="flex justify-end">
        <button
          className="btn-primary flex items-center gap-1.5"
          disabled={saveMutation.isPending}
          onClick={() => saveMutation.mutate()}
        >
          <Send size={14} /> Save sender identity
        </button>
      </div>
    </div>
  );
}
