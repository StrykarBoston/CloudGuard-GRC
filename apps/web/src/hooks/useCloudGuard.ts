import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export const cloudKeys = { accounts: ['accounts'] as const, findings: ['findings'] as const, dashboard: ['dashboard'] as const, compliance: ['compliance'] as const, scans: ['scans'] as const, settings: ['settings'] as const, auditLogs: ['audit-logs'] as const, organization: ['organization'] as const, organizationUsers: ['organization-users'] as const };
export function useAccounts() { return useQuery({ queryKey: cloudKeys.accounts, queryFn: api.accounts }); }
export function useFindings() { return useQuery({ queryKey: cloudKeys.findings, queryFn: api.findings }); }
export function useDashboard() { return useQuery({ queryKey: cloudKeys.dashboard, queryFn: api.dashboard }); }
export function useCompliance() { return useQuery({ queryKey: cloudKeys.compliance, queryFn: api.compliance }); }
export function useScans() { return useQuery({ queryKey: cloudKeys.scans, queryFn: api.scans, refetchInterval: (query) => query.state.data?.some(s => s.status === 'queued' || s.status === 'running') ? 750 : false }); }
export function useSettings() { return useQuery({ queryKey: cloudKeys.settings, queryFn: api.settings }); }
export function useOrganization() { return useQuery({ queryKey: cloudKeys.organization, queryFn: api.organization }); }
export function useOrganizationUsers() { return useQuery({ queryKey: cloudKeys.organizationUsers, queryFn: api.organizationUsers }); }
export function useAuditLogs() { return useQuery({ queryKey: cloudKeys.auditLogs, queryFn: api.auditLogs }); }
export function useOnboard() { const client = useQueryClient(); return useMutation({ mutationFn: api.onboard, onSuccess: () => client.invalidateQueries({ queryKey: cloudKeys.accounts }) }); }
export function useStartScan() { const client = useQueryClient(); return useMutation({ mutationFn: api.startScan, onSuccess: () => { client.invalidateQueries({ queryKey: cloudKeys.scans }); client.invalidateQueries({ queryKey: cloudKeys.findings }); client.invalidateQueries({ queryKey: cloudKeys.dashboard }); client.invalidateQueries({ queryKey: cloudKeys.compliance }); } }); }
export function useUpdateSettings() { const client = useQueryClient(); return useMutation({ mutationFn: api.updateSettings, onSuccess: () => { client.invalidateQueries({ queryKey: cloudKeys.settings }); client.invalidateQueries({ queryKey: cloudKeys.auditLogs }); } }); }
export function useDeleteAccount() { const client = useQueryClient(); return useMutation({ mutationFn: api.deleteAccount, onSuccess: () => { client.invalidateQueries({ queryKey: cloudKeys.accounts }); client.invalidateQueries({ queryKey: cloudKeys.findings }); client.invalidateQueries({ queryKey: cloudKeys.scans }); client.invalidateQueries({ queryKey: cloudKeys.dashboard }); client.invalidateQueries({ queryKey: cloudKeys.compliance }); client.invalidateQueries({ queryKey: cloudKeys.auditLogs }); } }); }
export function useFindingStatus() { const client = useQueryClient(); return useMutation({ mutationFn: ({ id, ...data }: { id: string; status?: 'OPEN' | 'RESOLVED' | 'SUPPRESSED'; assigned_to_user_id?: string | null; due_at?: string | null }) => api.updateFinding(id, data), onSuccess: () => { client.invalidateQueries({ queryKey: cloudKeys.findings }); client.invalidateQueries({ queryKey: cloudKeys.dashboard }); client.invalidateQueries({ queryKey: cloudKeys.compliance }); client.invalidateQueries({ queryKey: cloudKeys.auditLogs }); } }); }
