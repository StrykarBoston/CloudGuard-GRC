import { create } from 'zustand';
import { User } from '../types';
import { api } from '../services/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, pass: string) => Promise<boolean>;
  register: (organization: string, name: string, email: string, password: string) => Promise<boolean>;
  restore: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: Boolean(localStorage.getItem('access_token')),

  login: async (email: string, pass: string) => {
    const result = await api.login({ email, password: pass });
    localStorage.setItem('access_token', result.access_token);
    localStorage.setItem('refresh_token', result.refresh_token);
    set({ user: result.user, token: result.access_token, isAuthenticated: true });
    return true;
  },
  register: async (organization, name, email, password) => {
    const result = await api.register({ organization_name: organization, full_name: name, email, password });
    localStorage.setItem('access_token', result.access_token);
    localStorage.setItem('refresh_token', result.refresh_token);
    set({ user: result.user, token: result.access_token, isAuthenticated: true });
    return true;
  },
  restore: async () => {
    if (!localStorage.getItem('access_token')) return;
    try { set({ user: await api.me(), isAuthenticated: true }); } catch { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); set({ user: null, token: null, isAuthenticated: false }); }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
