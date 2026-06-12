import { Outlet, NavLink } from 'react-router-dom';
import {
  Users, MessageSquare, KanbanSquare, FormInput, Zap, Bot, Palette, Sparkles,
} from 'lucide-react';
import { SubAccountSwitcher } from './SubAccountSwitcher';
import { useBranding } from '../theme/ThemeProvider';
import { useSubAccountStore } from '../store/subAccountStore';

const navItems = [
  { to: '/pipeline', icon: KanbanSquare, label: 'Pipeline' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/conversations', icon: MessageSquare, label: 'Conversations' },
  { to: '/forms', icon: FormInput, label: 'Forms' },
  { to: '/automations', icon: Zap, label: 'Automations' },
  { to: '/receptionist', icon: Bot, label: 'AI Receptionist' },
  { to: '/branding', icon: Palette, label: 'Branding' },
];

export function Layout() {
  const branding = useBranding();
  const workspaceCount = useSubAccountStore((s) => s.subAccounts.length);

  return (
    <div className="flex h-screen bg-surface">
      {/* Sidebar */}
      <aside className="w-60 border-r border-edge flex flex-col bg-surface-raised/40">
        <div className="px-5 py-5 border-b border-edge flex items-center gap-3">
          {branding.logo_dark_url ? (
            <img
              src={branding.logo_dark_url}
              alt=""
              className="w-8 h-8 rounded-lg object-contain"
            />
          ) : (
            <span className="w-8 h-8 rounded-lg bg-primary/20 text-primary flex items-center justify-center shadow-glow-sm">
              <Sparkles size={16} />
            </span>
          )}
          <div className="min-w-0">
            <h1 className="text-base font-bold text-white tracking-tight truncate">
              <span className="text-primary">{branding.company_name.slice(0, 4)}</span>
              {branding.company_name.slice(4)}
            </h1>
            <p className="text-[10px] uppercase tracking-widest text-gray-500 mt-0.5">
              Own your platform
            </p>
          </div>
        </div>

        <nav className="mt-4 flex-1 px-2.5 space-y-0.5">
          <p className="panel-label px-2.5 pb-2">Workspace</p>
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 px-2.5 py-2 text-sm rounded-lg transition ${
                  isActive
                    ? 'bg-primary/15 text-white shadow-glow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-white/[0.04]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {/* Active rail */}
                  <span
                    className={`absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full transition ${
                      isActive ? 'bg-primary' : 'bg-transparent group-hover:bg-edge'
                    }`}
                  />
                  <Icon
                    size={16}
                    className={isActive ? 'text-primary' : 'text-gray-500 group-hover:text-gray-300'}
                  />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Isolation reminder, pinned to the bottom */}
        <div className="m-3 px-3.5 py-3 rounded-xl border border-edge bg-surface/60">
          <p className="text-[11px] font-medium text-gray-300">
            {workspaceCount || '—'} isolated workspace{workspaceCount === 1 ? '' : 's'}
          </p>
          <p className="text-[10px] text-gray-600 mt-0.5 leading-relaxed">
            Data never crosses between businesses.
          </p>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top navigation bar with the global workspace switcher */}
        <header className="h-16 shrink-0 border-b border-edge flex items-center justify-between px-6 gap-4 bg-surface/70 backdrop-blur-md">
          <SubAccountSwitcher />
          <div className="hidden md:flex items-center gap-2 text-xs text-gray-500">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            All data below is isolated to the selected workspace
          </div>
        </header>
        <main className="flex-1 overflow-auto animate-rise">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
