import { create } from 'zustand';
import { User } from '../types';
import { api, clearTokens, getAccessToken, setTokens } from '../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, pass: string, remember: boolean) => Promise<boolean>;
  register: (organization: string, name: string, email: string, password: string) => Promise<boolean>;
  restore: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getAccessToken(),
  isAuthenticated: Boolean(getAccessToken()),

  login: async (email: string, pass: string, remember: boolean) => {
    const result = await api.login({ email, password: pass });
    setTokens(result, remember);
    set({ user: result.user, token: result.access_token, isAuthenticated: true });
    return true;
  },
  register: async (organization, name, email, password) => {
    const result = await api.register({ organization_name: organization, full_name: name, email, password });
    setTokens(result, true);
    set({ user: result.user, token: result.access_token, isAuthenticated: true });
    return true;
  },
  restore: async () => {
    if (!getAccessToken()) return;
    try { set({ user: await api.me(), isAuthenticated: true }); } catch { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); set({ user: null, token: null, isAuthenticated: false }); }
  },

  logout: () => {
    clearTokens();
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
