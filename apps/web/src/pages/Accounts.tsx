import React from 'react';
import { CheckCircle2, Cloud, Loader2, Play, Plus, Trash2, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useAccounts, useDeleteAccount, useStartScan } from '../hooks/useCloudGuard';
import type { CloudAccount } from '../types';

const statusStyles: Record<CloudAccount['connection_status'], string> = {
  ACTIVE: 'border-passed/30 bg-passed/10 text-passed',
  ERROR: 'border-critical/30 bg-critical/10 text-critical',
  PENDING: 'border-medium/30 bg-medium/10 text-medium',
  DISCONNECTED: 'border-outline-variant bg-slate-100 text-on-surface-variant',
};

export const Accounts: React.FC = () => {
  const navigate = useNavigate();
  const { data: accounts = [], isLoading, error } = useAccounts();
  const { mutate: startScan, isPending: scanPending } = useStartScan();
  const { mutate: deleteAccount, isPending: deletePending } = useDeleteAccount();

  const removeAccount = (account: CloudAccount) => {
    if (window.confirm(`Disconnect ${account.account_alias}? Its saved scan history and findings will be removed from this local MVP.`)) deleteAccount(account.id);
  };

  return <div className="mx-auto max-w-7xl space-y-8">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><h1 className="text-3xl font-headline font-bold tracking-tight text-on-surface">Cloud Account Inventory</h1><p className="mt-1 text-sm text-on-surface-variant">Connected cloud environments audited under read-only policy boundaries.</p></div><button onClick={() => navigate('/accounts/onboard')} className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-on-primary shadow-sm shadow-blue-500/20 transition-colors hover:bg-primary-container"><Plus className="h-4 w-4" />Connect New Account</button></div>
    <div className="overflow-hidden rounded-2xl border border-outline-variant bg-surface p-6 shadow-xs">
      {isLoading && <div className="flex h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>}
      {error && <p className="text-sm text-critical">Unable to load accounts. Please sign in again.</p>}
      {!isLoading && !error && accounts.length === 0 && <p className="text-sm text-on-surface-variant">No AWS accounts are connected. Connect a read-only IAM role to begin.</p>}
      {accounts.length > 0 && <div className="overflow-x-auto"><table className="w-full whitespace-nowrap text-left text-xs"><thead className="border-b border-outline-variant bg-slate-50 font-label uppercase tracking-wider text-on-surface-variant"><tr><th className="px-4 py-3">Provider</th><th className="px-4 py-3">Account Alias</th><th className="px-4 py-3">Account ID</th><th className="px-4 py-3">Assumed Role ARN</th><th className="px-4 py-3">Status</th><th className="px-4 py-3 text-right">Actions</th></tr></thead><tbody className="divide-y divide-outline-variant/60">{accounts.map((account) => <tr key={account.id} className="transition-colors hover:bg-blue-50/40"><td className="px-4 py-3.5"><span className="inline-flex items-center gap-1.5 rounded border border-blue-200 bg-blue-50 px-2.5 py-1 font-bold text-primary"><Cloud className="h-3.5 w-3.5" />{account.provider}</span></td><td className="px-4 py-3.5 text-sm font-medium text-on-surface">{account.account_alias}</td><td className="px-4 py-3.5 font-mono text-on-surface-variant">{account.account_number}</td><td className="max-w-xs truncate px-4 py-3.5 font-mono text-on-surface-variant" title={account.role_arn}>{account.role_arn}</td><td className="px-4 py-3.5"><span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${statusStyles[account.connection_status]}`}>{account.connection_status === 'ACTIVE' ? <CheckCircle2 className="h-3.5 w-3.5" /> : <XCircle className="h-3.5 w-3.5" />}{account.connection_status}</span></td><td className="px-4 py-3.5 text-right"><div className="flex justify-end gap-2"><button onClick={() => startScan(account.id)} disabled={scanPending || account.connection_status !== 'ACTIVE'} className="inline-flex items-center gap-1 rounded-lg border border-primary/30 bg-primary/10 px-2.5 py-1.5 font-semibold text-primary disabled:cursor-not-allowed disabled:opacity-50"><Play className="h-3.5 w-3.5" />Scan now</button><button onClick={() => removeAccount(account)} disabled={deletePending} title={`Disconnect ${account.account_alias}`} className="rounded-lg border border-critical/30 bg-critical/10 p-1.5 text-critical disabled:opacity-50"><Trash2 className="h-3.5 w-3.5" /></button></div></td></tr>)}</tbody></table></div>}
    </div>
  </div>;
};
