import React from 'react';
import { Bell, Loader2, Shield } from 'lucide-react';

import { useOrganization, useSettings, useUpdateSettings } from '../hooks/useCloudGuard';

export const Settings: React.FC = () => {
  const { data: organization, isLoading: organizationLoading } = useOrganization();
  const { data: settings, isLoading: settingsLoading, error: settingsError } = useSettings();
  const { mutate: updateSettings, isPending, error: updateError } = useUpdateSettings();

  if (organizationLoading || settingsLoading) {
    return <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>;
  }

  if (!settings || settingsError) {
    return <div className="rounded-xl border border-critical/30 bg-critical/10 p-4 text-sm text-critical">Unable to load organization settings. Refresh the page or sign in again.</div>;
  }

  const update = (patch: Parameters<typeof updateSettings>[0]) => updateSettings(patch);

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-3xl font-headline font-bold tracking-tight text-on-surface">Organization &amp; Settings</h1>
        <p className="mt-1 text-sm text-on-surface-variant">Manage tenant configuration, security policies, and scan schedules.</p>
      </div>

      {updateError && <div className="rounded-xl border border-critical/30 bg-critical/10 p-4 text-sm text-critical">{updateError instanceof Error ? updateError.message : 'Unable to save settings.'}</div>}

      <section className="space-y-4 rounded-2xl border border-outline-variant bg-surface p-6 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary"><Shield className="h-4 w-4" /></div>
          <h2 className="text-base font-headline font-semibold text-on-surface">Tenant &amp; Organization Profile</h2>
        </div>
        <div className="grid grid-cols-1 gap-4 text-xs font-label sm:grid-cols-2">
          <Info label="Company Name" value={organization?.name ?? 'Unavailable'} />
          <Info label="Plan" value="Open-source MVP" accent />
          <Info label="Tenant ID" value={organization?.id ?? 'Unavailable'} mono />
          <Info label="Created" value={organization ? new Date(organization.created_at).toLocaleDateString() : 'Unavailable'} />
        </div>
      </section>

      <section className="space-y-4 rounded-2xl border border-outline-variant bg-surface p-6 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-primary"><Bell className="h-4 w-4" /></div>
          <h2 className="text-base font-headline font-semibold text-on-surface">Scan Schedules &amp; Alerts</h2>
        </div>

        <ToggleRow title="Daily automated scan" description="Runs read-only posture checks across each connected account." checked={settings.daily_scans_enabled} disabled={isPending || !settings.scheduled_scans_available} onChange={(daily_scans_enabled) => update({ daily_scans_enabled })} />
        <label className="flex items-center justify-between gap-4 rounded-xl border border-outline-variant bg-slate-50 p-3.5 text-xs">
          <span><span className="block font-semibold text-on-surface">Daily scan time (UTC)</span><span className="mt-0.5 block text-[11px] text-on-surface-variant">The background worker starts eligible scans during this hour.</span></span>
          <select aria-label="Daily scan hour in UTC" value={settings.daily_scan_hour_utc} disabled={isPending || !settings.daily_scans_enabled} onChange={(event) => update({ daily_scan_hour_utc: Number(event.target.value) })} className="rounded-lg border border-outline-variant bg-surface px-2 py-1.5 font-mono text-on-surface disabled:cursor-not-allowed disabled:opacity-60">
            {Array.from({ length: 24 }, (_, hour) => <option key={hour} value={hour}>{String(hour).padStart(2, '0')}:00</option>)}
          </select>
        </label>
        <ToggleRow title="Slack webhook alerts" description={settings.slack_webhook_configured ? 'Notify the configured channel for new critical findings.' : 'A server administrator must configure the Slack webhook before this can be enabled.'} checked={settings.slack_alerts_enabled} disabled={isPending || !settings.slack_webhook_configured} onChange={(slack_alerts_enabled) => update({ slack_alerts_enabled })} />
      </section>
    </div>
  );
};

function Info({ label, value, mono, accent = false }: { label: string; value: string; mono?: boolean; accent?: boolean }) {
  return <div><span className="mb-1 block text-on-surface-variant">{label}</span><div className={`rounded-lg border border-outline-variant p-2.5 font-medium ${mono ? 'font-mono text-on-surface-variant' : accent ? 'border-blue-200 bg-blue-50/60 text-primary' : 'bg-slate-50 text-on-surface'}`}>{value}</div></div>;
}

function ToggleRow({ title, description, checked, disabled, onChange }: { title: string; description: string; checked: boolean; disabled: boolean; onChange: (value: boolean) => void }) {
  return <label className="flex items-center justify-between gap-4 rounded-xl border border-outline-variant bg-slate-50 p-3.5 transition-colors hover:bg-blue-50/30"><span><span className="block text-xs font-semibold text-on-surface">{title}</span><span className="mt-0.5 block text-[11px] text-on-surface-variant">{description}</span></span><input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} className="h-4 w-4 cursor-pointer accent-primary disabled:cursor-not-allowed" /></label>;
}
