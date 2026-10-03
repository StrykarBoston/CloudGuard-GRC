import React from 'react';
import { History, Loader2 } from 'lucide-react';

import { useAuditLogs } from '../hooks/useCloudGuard';

export const AuditLog: React.FC = () => {
  const { data: events = [], isLoading, error } = useAuditLogs();

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <header><h1 className="text-3xl font-headline font-bold tracking-tight text-on-surface">Audit log</h1><p className="mt-1 text-sm text-on-surface-variant">Immutable, tenant-scoped records of CloudGuard security-relevant activity.</p></header>
      <section className="overflow-hidden rounded-2xl border border-outline-variant bg-surface shadow-xs">
        {isLoading && <div className="flex h-48 items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div>}
        {error && <p className="m-6 rounded-xl border border-critical/30 bg-critical/10 p-4 text-sm text-critical">Unable to load audit events. Please sign in again or retry.</p>}
        {!isLoading && !error && events.length === 0 && <div className="flex flex-col items-center gap-3 p-12 text-center text-on-surface-variant"><History className="h-8 w-8 text-primary" /><p className="text-sm">No audit events have been recorded for this organization yet.</p></div>}
        {!isLoading && !error && events.length > 0 && <div className="overflow-x-auto"><table className="w-full text-left text-xs"><thead className="border-b border-outline-variant bg-slate-50 text-on-surface-variant"><tr><th className="px-4 py-3 font-semibold">Timestamp</th><th className="px-4 py-3 font-semibold">Event</th><th className="px-4 py-3 font-semibold">Actor ID</th><th className="px-4 py-3 font-semibold">Details</th></tr></thead><tbody className="divide-y divide-outline-variant/60">{events.map((event) => <tr key={event.id} className="hover:bg-blue-50/40"><td className="whitespace-nowrap px-4 py-3.5 font-mono text-on-surface-variant">{new Date(event.created_at).toLocaleString()}</td><td className="px-4 py-3.5 font-semibold text-on-surface">{event.event_type}</td><td className="px-4 py-3.5 font-mono text-on-surface-variant">{event.actor_id ?? 'System'}</td><td className="max-w-lg px-4 py-3.5 font-mono text-[11px] text-on-surface-variant break-all">{JSON.stringify(event.details)}</td></tr>)}</tbody></table></div>}
      </section>
    </div>
  );
};
