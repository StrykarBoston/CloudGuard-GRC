import axios from 'axios';
import type { AuditLog, CloudAccount, Finding, GRCFramework, Organization, TenantSettings, ThreatScoreSummary, User } from '../types';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

let isRefreshing = false;
let refreshSubscribers: ((error: unknown) => void)[] = [];

const onRefreshed = (error: unknown) => {
  refreshSubscribers.forEach((cb) => cb(error));
  refreshSubscribers = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config as (typeof error.config & { _retry?: boolean }) | undefined;
    if (error.response?.status === 401 && config && !config._retry && !config.url?.includes('/auth/')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          refreshSubscribers.push((err: unknown) => {
            if (err) return reject(err);
            resolve(apiClient(config));
          });
        });
      }

      config._retry = true;
      isRefreshing = true;

      try {
        await apiClient.post('/auth/refresh', {});
        isRefreshing = false;
        onRefreshed(null);
        return apiClient(config);
      } catch (refreshError) {
        isRefreshing = false;
        onRefreshed(refreshError);
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export interface Tokens { user: User }
export interface Scan { id: string; cloud_account_id: string; status: string; progress: number; partial: boolean; error_summary: string | null; created_at: string }
export const api = {
  register: (data: { organization_name: string; full_name: string; email: string; password: string }) => apiClient.post<Tokens>('/auth/register', data).then(r => r.data),
  login: (data: { email: string; password: string; remember_me: boolean }) => apiClient.post<Tokens>('/auth/login', data).then(r => r.data),
  forgotPassword: (email: string) =>
    apiClient.post<{ message: string; reset_token?: string }>('/auth/forgot-password', { email }).then(r => r.data),
  verifyResetToken: (token: string) =>
    apiClient.get<{ valid: boolean; email: string }>('/auth/reset-password/verify', { params: { token } }).then(r => r.data),
  resetPassword: (data: { token: string; new_password: string }) =>
    apiClient.post<{ status: string; message: string }>('/auth/reset-password', data).then(r => r.data),
  logout: () => apiClient.post('/auth/logout').then(r => r.data),
  me: () => apiClient.get<User>('/auth/me').then(r => r.data),
  accounts: () => apiClient.get<CloudAccount[]>('/cloud-accounts').then(r => r.data),
  deleteAccount: (id: string) => apiClient.delete(`/cloud-accounts/${id}`),
  onboard: (data: { account_alias: string; account_number: string; role_arn: string; external_id: string }) => apiClient.post<CloudAccount>('/cloud-accounts/onboard', data).then(r => r.data),
  scans: () => apiClient.get<Scan[]>('/scans').then(r => r.data),
  startScan: (cloud_account_id: string) => apiClient.post<Scan>('/scans', { cloud_account_id }).then(r => r.data),
  findings: () => apiClient.get<Finding[]>('/findings').then(r => r.data),
  updateFinding: (id: string, data: Partial<Pick<Finding, 'status' | 'assigned_to_user_id' | 'due_at'>>) => apiClient.patch<Finding>(`/findings/${id}`, data).then(r => r.data),
  organization: () => apiClient.get<Organization>('/organization').then(r => r.data),
  organizationUsers: () => apiClient.get<User[]>('/organization/users').then(r => r.data),
  settings: () => apiClient.get<TenantSettings>('/settings').then(r => r.data),
  updateSettings: (data: Partial<Pick<TenantSettings, 'daily_scans_enabled' | 'daily_scan_hour_utc' | 'slack_alerts_enabled'>>) => apiClient.put<TenantSettings>('/settings', data).then(r => r.data),
  auditLogs: () => apiClient.get<AuditLog[]>('/audit-logs').then(r => r.data),
  dashboard: () => apiClient.get<ThreatScoreSummary>('/dashboard').then(r => r.data),
  compliance: () => apiClient.get<GRCFramework[]>('/compliance').then(r => r.data),
  reportUrl: () => `${apiClient.defaults.baseURL}/reports/summary`,
  exportReport: (frameworkId?: string) =>
    apiClient.get(`/reports/compliance/${frameworkId || 'all'}/export`, { responseType: 'blob' }).then(r => r.data),
  exportPdf: (frameworkId?: string) =>
    apiClient.get(`/reports/compliance/${frameworkId || 'all'}/export.pdf`, { responseType: 'blob' }).then(r => r.data),
};
