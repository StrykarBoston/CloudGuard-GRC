import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export const cloudKeys = { accounts: ['accounts'] as const, findings: ['findings'] as const, dashboard: ['dashboard'] as const, compliance: ['compliance'] as const, scans: ['scans'] as const };
export function useAccounts() { return useQuery({ queryKey: cloudKeys.accounts, queryFn: api.accounts }); }
export function useFindings() { return useQuery({ queryKey: cloudKeys.findings, queryFn: api.findings }); }
export function useDashboard() { return useQuery({ queryKey: cloudKeys.dashboard, queryFn: api.dashboard }); }
export function useCompliance() { return useQuery({ queryKey: cloudKeys.compliance, queryFn: api.compliance }); }
export function useScans() { return useQuery({ queryKey: cloudKeys.scans, queryFn: api.scans, refetchInterval: (query) => query.state.data?.some(s => s.status === 'queued' || s.status === 'running') ? 750 : false }); }
export function useOnboard() { const client = useQueryClient(); return useMutation({ mutationFn: api.onboard, onSuccess: () => client.invalidateQueries({ queryKey: cloudKeys.accounts }) }); }
export function useStartScan() { const client = useQueryClient(); return useMutation({ mutationFn: api.startScan, onSuccess: () => { client.invalidateQueries({ queryKey: cloudKeys.scans }); client.invalidateQueries({ queryKey: cloudKeys.findings }); client.invalidateQueries({ queryKey: cloudKeys.dashboard }); client.invalidateQueries({ queryKey: cloudKeys.compliance }); } }); }
export function useFindingStatus() { const client = useQueryClient(); return useMutation({ mutationFn: ({ id, status }: { id: string; status: 'OPEN' | 'RESOLVED' | 'SUPPRESSED' }) => api.updateFinding(id, status), onSuccess: () => { client.invalidateQueries({ queryKey: cloudKeys.findings }); client.invalidateQueries({ queryKey: cloudKeys.dashboard }); client.invalidateQueries({ queryKey: cloudKeys.compliance }); } }); }
