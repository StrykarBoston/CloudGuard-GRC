import { create } from 'zustand';
import { User } from '../types';
import { api } from '../services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isRestoring: boolean;
  login: (email: string, pass: string, remember: boolean) => Promise<boolean>;
  register: (organization: string, name: string, email: string, password: string) => Promise<boolean>;
  restore: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isRestoring: true,

  login: async (email: string, pass: string, remember: boolean) => {
    const result = await api.login({ email, password: pass, remember_me: remember });
    set({ user: result.user, isAuthenticated: true });
    return true;
  },
  register: async (organization, name, email, password) => {
    const result = await api.register({ organization_name: organization, full_name: name, email, password });
    set({ user: result.user, isAuthenticated: true });
    return true;
  },
  restore: async () => {
    try { 
      const user = await api.me();
      set({ user, isAuthenticated: true, isRestoring: false }); 
    } catch { 
      set({ user: null, isAuthenticated: false, isRestoring: false }); 
    }
  },

  logout: async () => {
    try { await api.logout(); } catch { /* Ignore */ }
    set({ user: null, isAuthenticated: false });
  },
}));
