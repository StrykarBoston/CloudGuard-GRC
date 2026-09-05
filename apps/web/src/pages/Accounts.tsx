import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAccounts } from '../hooks/useCloudGuard';
import { Cloud, Plus, CheckCircle2 } from 'lucide-react';

export const Accounts: React.FC = () => {
  const navigate = useNavigate();
  const { data: accounts = [], isLoading, error } = useAccounts();

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-headline font-bold text-on-surface tracking-tight">
            Cloud Account Inventory
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">
            Connected cloud environments actively audited under read-only policy boundaries.
          </p>
        </div>

        <button
          onClick={() => navigate('/accounts/onboard')}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary font-label font-semibold rounded-lg text-xs hover:bg-primary-container transition-colors shadow-[0_0_12px_rgba(0,212,255,0.2)]"
        >
          <Plus className="w-4 h-4" />
          <span>Connect New Account</span>
        </button>
      </div>

      <div className="bg-surface-container/50 backdrop-blur-sm border border-outline-variant/60 rounded-2xl p-6 shadow-lg">
        {isLoading && <p className="text-sm text-on-surface-variant">Loading connected accounts…</p>}
        {error && <p className="text-sm text-critical">Unable to load accounts. Please sign in again.</p>}
        {!isLoading && !error && accounts.length === 0 && <p className="text-sm text-on-surface-variant">No cloud accounts are connected. Add a local simulated AWS account to begin.</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs whitespace-nowrap">
            <thead className="bg-surface-container-low text-on-surface-variant font-medium font-label border-b border-outline-variant/50">
              <tr>
                <th className="py-3 px-4">Provider</th>
                <th className="py-3 px-4">Account Alias</th>
                <th className="py-3 px-4">Account ID</th>
                <th className="py-3 px-4">Assumed Role ARN</th>
                <th className="py-3 px-4">External ID</th>
                <th className="py-3 px-4 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/30">
              {accounts.map((acc) => (
                <tr key={acc.id} className="hover:bg-surface-container-high/40 transition-colors">
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container text-primary font-headline font-bold border border-primary/20 text-xs">
                      <Cloud className="w-3.5 h-3.5" />
                      {acc.provider}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-medium text-sm text-on-surface">
                    {acc.account_alias}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-on-surface-variant">
                    {acc.account_number}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-on-surface-variant max-w-xs truncate">
                    {acc.role_arn}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-primary">
                    {acc.external_id}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-passed/10 text-passed border border-passed/30 text-[11px] font-label font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {acc.connection_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
