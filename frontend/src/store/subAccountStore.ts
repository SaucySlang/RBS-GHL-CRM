import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface SubAccount {
  id: string;
  agency_id: string;
  name: string;
  industry_type: string;
  logo_url: string | null;
  custom_domain: string | null;
  timezone: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
  from_name: string | null;
  reply_to_email: string | null;
  twilio_phone_number: string | null;
  owner_email: string | null;
  owner_phone: string | null;
  created_at: string;
}

interface SubAccountState {
  activeSubAccountId: string | null;
  subAccounts: SubAccount[];
  setSubAccounts: (subAccounts: SubAccount[]) => void;
  setActiveSubAccount: (id: string) => void;
  activeSubAccount: () => SubAccount | undefined;
}

export const useSubAccountStore = create<SubAccountState>()(
  persist(
    (set, get) => ({
      activeSubAccountId: null,
      subAccounts: [],
      setSubAccounts: (subAccounts) => {
        set({ subAccounts });
        // Auto-select the first workspace on first load
        const { activeSubAccountId } = get();
        const stillExists = subAccounts.some((s) => s.id === activeSubAccountId);
        if ((!activeSubAccountId || !stillExists) && subAccounts.length > 0) {
          set({ activeSubAccountId: subAccounts[0].id });
        }
      },
      setActiveSubAccount: (id) => set({ activeSubAccountId: id }),
      activeSubAccount: () =>
        get().subAccounts.find((s) => s.id === get().activeSubAccountId),
    }),
    { name: 'leadstack-sub-account' }
  )
);

/** Read the active workspace id outside React (axios interceptor). */
export function getActiveSubAccountId(): string | null {
  return useSubAccountStore.getState().activeSubAccountId;
}
