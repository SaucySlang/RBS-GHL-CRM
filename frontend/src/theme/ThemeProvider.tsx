import {
  createContext, useContext, useEffect, ReactNode,
} from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Branding {
  company_name: string;
  logo_dark_url: string | null;
  logo_light_url: string | null;
  primary_color: string;
  accent_color: string;
  custom_domain: string | null;
}

const DEFAULT_BRANDING: Branding = {
  company_name: 'LeadStack',
  logo_dark_url: null,
  logo_light_url: null,
  primary_color: '#8B5CF6',
  accent_color: '#C084FC',
  custom_domain: null,
};

const BrandingContext = createContext<Branding>(DEFAULT_BRANDING);

export const useBranding = () => useContext(BrandingContext);

/** "#8B5CF6" -> "139 92 246" for rgb(var(--x) / alpha) Tailwind tokens. */
function hexToRgbTriple(hex: string): string | null {
  const m = /^#([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return null;
  const n = parseInt(m[1], 16);
  return `${(n >> 16) & 255} ${(n >> 8) & 255} ${n & 255}`;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { data } = useQuery({
    queryKey: ['branding'],
    queryFn: () =>
      axios.get<Branding>(`${API_BASE}/api/v1/public/branding`).then((r) => r.data),
    staleTime: 60_000,
  });

  const branding = data ?? DEFAULT_BRANDING;

  // Bind the whole visual identity to CSS custom properties at runtime.
  useEffect(() => {
    const root = document.documentElement;
    const primary = hexToRgbTriple(branding.primary_color);
    const accent = hexToRgbTriple(branding.accent_color);
    if (primary) root.style.setProperty('--color-primary', primary);
    if (accent) root.style.setProperty('--color-accent', accent);
    document.title = branding.company_name;
  }, [branding]);

  return (
    <BrandingContext.Provider value={branding}>{children}</BrandingContext.Provider>
  );
}
