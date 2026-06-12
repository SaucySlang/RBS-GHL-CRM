import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Building2, Check, ChevronsUpDown } from 'lucide-react';
import { subAccountsApi } from '../api/client';
import { useSubAccountStore } from '../store/subAccountStore';

const INDUSTRY_LABELS: Record<string, string> = {
  real_estate: 'Real Estate',
  music_production: 'Music Production',
  ecommerce: 'E-commerce',
  ai_consulting: 'AI Consulting',
  other: 'General',
};

export function SubAccountSwitcher() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { subAccounts, activeSubAccountId, setSubAccounts, setActiveSubAccount } =
    useSubAccountStore();

  const { data } = useQuery({
    queryKey: ['sub-accounts'],
    queryFn: () => subAccountsApi.list(),
    select: (res) => res.data,
  });

  useEffect(() => {
    if (data) setSubAccounts(data);
  }, [data, setSubAccounts]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const active = subAccounts.find((s) => s.id === activeSubAccountId);

  const switchTo = (id: string) => {
    setActiveSubAccount(id);
    setOpen(false);
    // Every cached query belongs to the previous workspace — drop it all.
    queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== 'sub-accounts' });
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2.5 px-3 py-2 card hover:border-primary/60 transition min-w-[220px]"
      >
        {active?.logo_url ? (
          <img src={active.logo_url} alt="" className="w-6 h-6 rounded object-cover" />
        ) : (
          <span className="w-6 h-6 rounded bg-primary/20 text-primary flex items-center justify-center">
            <Building2 size={14} />
          </span>
        )}
        <span className="flex-1 text-left">
          <span className="block text-sm font-medium text-white leading-tight">
            {active?.name ?? 'Select workspace'}
          </span>
          <span className="block text-[11px] text-gray-500 leading-tight">
            {active ? INDUSTRY_LABELS[active.industry_type] ?? active.industry_type : '—'}
          </span>
        </span>
        <ChevronsUpDown size={15} className="text-gray-500" />
      </button>

      {open && (
        <div className="absolute z-50 mt-2 w-full bg-surface-overlay border border-edge rounded-xl shadow-glow overflow-hidden">
          <p className="px-3 pt-2.5 pb-1 text-[10px] uppercase tracking-widest text-gray-500">
            Workspaces
          </p>
          {subAccounts.map((sa) => (
            <button
              key={sa.id}
              onClick={() => switchTo(sa.id)}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-primary/10 transition text-left"
            >
              <span className="w-6 h-6 rounded bg-primary/20 text-primary flex items-center justify-center">
                <Building2 size={13} />
              </span>
              <span className="flex-1">
                <span className="block text-sm text-gray-200">{sa.name}</span>
                <span className="block text-[11px] text-gray-500">
                  {INDUSTRY_LABELS[sa.industry_type] ?? sa.industry_type}
                </span>
              </span>
              {sa.id === activeSubAccountId && <Check size={15} className="text-primary" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
