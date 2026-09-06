import React from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { Shield, Bell } from 'lucide-react';

export const Settings: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-headline font-bold text-on-surface tracking-tight">
          Organization & Settings
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Manage tenant configuration, security policies, and scan schedules.
        </p>
      </div>

      <div className="space-y-6">
        {/* Tenant Details */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <Shield className="w-4 h-4" />
            </div>
            <h2 className="text-base font-headline font-semibold text-on-surface">
              Tenant & Organization Profile
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-label">
            <div>
              <span className="text-on-surface-variant block mb-1">Company Name</span>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-outline-variant text-on-surface font-medium">
                CloudGuard Demo Enterprise
              </div>
            </div>
            <div>
              <span className="text-on-surface-variant block mb-1">Current Plan</span>
              <div className="p-2.5 bg-blue-50/60 rounded-lg border border-blue-200 text-primary font-bold">
                Enterprise Open-Source / Prototype Tier
              </div>
            </div>
            <div>
              <span className="text-on-surface-variant block mb-1">Tenant ID (UUID)</span>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-outline-variant font-mono text-on-surface-variant">
                {user?.tenant_id || 'ten-88219034-4bc1-901a'}
              </div>
            </div>
            <div>
              <span className="text-on-surface-variant block mb-1">Current User Role</span>
              <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200 text-passed font-semibold">
                {user?.role || 'SUPER_ADMIN'}
              </div>
            </div>
          </div>
        </div>

        {/* Scan Automation Schedule */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-primary">
              <Bell className="w-4 h-4" />
            </div>
            <h2 className="text-base font-headline font-semibold text-on-surface">
              Scan Schedules & Continuous Auditing
            </h2>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3.5 bg-slate-50 hover:bg-blue-50/30 rounded-xl border border-outline-variant transition-colors">
              <div>
                <p className="font-semibold text-on-surface">Daily Automated Scan</p>
                <p className="text-on-surface-variant text-[11px] mt-0.5">
                  Executes read-only CIS and DPDPA posture evaluation across all connected accounts.
                </p>
              </div>
              <input type="checkbox" defaultChecked className="accent-primary w-4 h-4 cursor-pointer" />
            </div>

            <div className="flex items-center justify-between p-3.5 bg-slate-50 hover:bg-blue-50/30 rounded-xl border border-outline-variant transition-colors">
              <div>
                <p className="font-semibold text-on-surface">Slack Webhook Alerts</p>
                <p className="text-on-surface-variant text-[11px] mt-0.5">
                  Immediately notifies designated channel on any new CRITICAL finding.
                </p>
              </div>
              <input type="checkbox" defaultChecked className="accent-primary w-4 h-4 cursor-pointer" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
