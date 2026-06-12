import { Outlet, NavLink } from 'react-router-dom';
import {
  Users, MessageSquare, KanbanSquare, FormInput, Zap, Bot, Palette,
} from 'lucide-react';
import { SubAccountSwitcher } from './SubAccountSwitcher';
import { useBranding } from '../theme/ThemeProvider';

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

  return (
    <div className="flex h-screen bg-surface">
      {/* Sidebar */}
      <aside className="w-60 border-r border-edge flex flex-col">
        <div className="px-5 py-5 border-b border-edge flex items-center gap-2.5">
          {branding.logo_dark_url && (
            <img
              src={branding.logo_dark_url}
              alt=""
              className="w-7 h-7 rounded object-contain"
            />
          )}
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">
              <span className="text-primary">{branding.company_name.slice(0, 4)}</span>
              {branding.company_name.slice(4)}
            </h1>
            <p className="text-[11px] text-gray-500 mt-0.5">Own your platform</p>
          </div>
        </div>
        <nav className="mt-3 flex-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-2.5 text-sm transition border-l-2 ${
                  isActive
                    ? 'border-primary bg-primary/10 text-white'
                    : 'border-transparent text-gray-400 hover:text-white hover:bg-surface-raised'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top navigation bar with the global workspace switcher */}
        <header className="h-16 border-b border-edge flex items-center justify-between px-6 gap-4">
          <SubAccountSwitcher />
          <div className="text-xs text-gray-500">
            All data below is isolated to the selected workspace
          </div>
        </header>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
