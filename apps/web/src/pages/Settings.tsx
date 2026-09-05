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
        <div className="bg-surface-container/50 border border-outline-variant/60 rounded-2xl p-6 shadow-lg space-y-4">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-5 h-5 text-primary" />
            <h2 className="text-base font-headline font-semibold text-on-surface">
              Tenant & Organization Profile
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-label">
            <div>
              <span className="text-on-surface-variant block mb-1">Company Name</span>
              <div className="p-2.5 bg-surface rounded-lg border border-outline-variant/60 text-on-surface font-medium">
                CloudGuard Demo Enterprise
              </div>
            </div>
            <div>
              <span className="text-on-surface-variant block mb-1">Current Plan</span>
              <div className="p-2.5 bg-surface rounded-lg border border-outline-variant/60 text-primary font-bold">
                Enterprise Open-Source / Prototype Tier
              </div>
            </div>
            <div>
              <span className="text-on-surface-variant block mb-1">Tenant ID (UUID)</span>
              <div className="p-2.5 bg-surface rounded-lg border border-outline-variant/60 font-mono text-on-surface-variant">
                {user?.tenant_id || 'ten-88219034-4bc1-901a'}
              </div>
            </div>
            <div>
              <span className="text-on-surface-variant block mb-1">Current User Role</span>
              <div className="p-2.5 bg-surface rounded-lg border border-outline-variant/60 text-passed font-medium">
                {user?.role || 'SUPER_ADMIN'}
              </div>
            </div>
          </div>
        </div>

        {/* Scan Automation Schedule */}
        <div className="bg-surface-container/50 border border-outline-variant/60 rounded-2xl p-6 shadow-lg space-y-4">
          <div className="flex items-center gap-3 mb-2">
            <Bell className="w-5 h-5 text-secondary" />
            <h2 className="text-base font-headline font-semibold text-on-surface">
              Scan Schedules & Continuous Auditing
            </h2>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg border border-outline-variant/40">
              <div>
                <p className="font-medium text-on-surface">Daily Automated Scan</p>
                <p className="text-on-surface-variant text-[11px]">
                  Executes read-only CIS and DPDPA posture evaluation across all connected accounts.
                </p>
              </div>
              <input type="checkbox" defaultChecked className="accent-primary w-4 h-4" />
            </div>

            <div className="flex items-center justify-between p-3 bg-surface-container-low rounded-lg border border-outline-variant/40">
              <div>
                <p className="font-medium text-on-surface">Slack Webhook Alerts</p>
                <p className="text-on-surface-variant text-[11px]">
                  Immediately notifies designated channel on any new CRITICAL finding.
                </p>
              </div>
              <input type="checkbox" defaultChecked className="accent-primary w-4 h-4" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
