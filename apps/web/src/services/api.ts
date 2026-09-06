import axios from 'axios';
import type { CloudAccount, Finding, GRCFramework, ThreatScoreSummary, User } from '../types';

const refreshClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export const getAccessToken = () => localStorage.getItem('access_token') || sessionStorage.getItem('access_token');

export const setTokens = (tokens: Tokens, remember: boolean) => {
  const storage = remember ? localStorage : sessionStorage;
  const otherStorage = remember ? sessionStorage : localStorage;
  otherStorage.removeItem('access_token');
  otherStorage.removeItem('refresh_token');
  storage.setItem('access_token', tokens.access_token);
  storage.setItem('refresh_token', tokens.refresh_token);
};

export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
};

let refreshRequest: Promise<Tokens> | null = null;

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const config = error.config as (typeof error.config & { _retry?: boolean }) | undefined;
    if (error.response?.status === 401 && config && !config._retry && !config.url?.includes('/auth/')) {
      config._retry = true;
      const refreshToken = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
      if (refreshToken) {
        refreshRequest ??= refreshClient.post<Tokens>('/auth/refresh', { refresh_token: refreshToken }).then((response) => {
          const remember = Boolean(localStorage.getItem('refresh_token'));
          setTokens(response.data, remember);
          return response.data;
        }).finally(() => { refreshRequest = null; });
        return refreshRequest.then((tokens) => {
          config.headers.Authorization = `Bearer ${tokens.access_token}`;
          return apiClient(config);
        }).catch(() => {
          clearTokens();
          return Promise.reject(error);
        });
      }
    }
    console.error('API Error Response:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface Tokens { access_token: string; refresh_token: string; user: User }
export interface Scan { id: string; cloud_account_id: string; status: string; progress: number; partial: boolean; error_summary: string | null; created_at: string }
export const api = {
  register: (data: { organization_name: string; full_name: string; email: string; password: string }) => apiClient.post<Tokens>('/auth/register', data).then(r => r.data),
  login: (data: { email: string; password: string }) => apiClient.post<Tokens>('/auth/login', data).then(r => r.data),
  me: () => apiClient.get<User>('/auth/me').then(r => r.data),
  accounts: () => apiClient.get<CloudAccount[]>('/cloud-accounts').then(r => r.data),
  onboard: (data: { account_alias: string; account_number: string; role_arn: string; external_id: string; validation_mode: 'local_mock' }) => apiClient.post<CloudAccount>('/cloud-accounts/onboard', data).then(r => r.data),
  scans: () => apiClient.get<Scan[]>('/scans').then(r => r.data),
  startScan: (cloud_account_id: string) => apiClient.post<Scan>('/scans', { cloud_account_id }).then(r => r.data),
  findings: () => apiClient.get<Finding[]>('/findings').then(r => r.data),
  updateFinding: (id: string, status: 'OPEN' | 'RESOLVED' | 'SUPPRESSED') => apiClient.patch<Finding>(`/findings/${id}`, { status }).then(r => r.data),
  dashboard: () => apiClient.get<ThreatScoreSummary>('/dashboard').then(r => r.data),
  compliance: () => apiClient.get<GRCFramework[]>('/compliance').then(r => r.data),
  reportUrl: () => `${apiClient.defaults.baseURL}/reports/summary`,
  exportReport: (frameworkId?: string) =>
    apiClient.get(`/reports/compliance/${frameworkId || 'all'}/export`, { responseType: 'blob' }).then(r => r.data),
};
