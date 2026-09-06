import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useScanStore } from '../store/useScanStore';
import { useDashboard, useFindings, useCompliance } from '../hooks/useCloudGuard';
import {
  Shield,
  AlertTriangle,
  Cloud,
  FileCheck2,
  TrendingUp,
  ArrowRight,
  ExternalLink,
  Loader2,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { selectFinding } = useScanStore();
  const { data: threatSummary, isLoading: isDashLoading } = useDashboard();
  const { data: findings = [], isLoading: isFindingsLoading } = useFindings();
  const { data: frameworks = [], isLoading: isFrameworksLoading } = useCompliance();

  if (isDashLoading || isFindingsLoading || isFrameworksLoading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
  }

  if (!threatSummary) return null;

  const handleViewFix = (finding: (typeof findings)[0]) => {
    selectFinding(finding);
    navigate('/findings');
  };

  const criticalAndHigh = findings.filter(
    (f) => f.severity === 'CRITICAL' || f.severity === 'HIGH'
  );

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Page Header */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-headline font-bold text-on-surface tracking-tight">
            Security Posture
          </h1>
          <p className="text-on-surface-variant text-sm mt-1">
            Real-time compliance and risk posture across your connected AWS infrastructure.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-label bg-passed/10 text-passed border border-passed/30">
            <span className="w-1.5 h-1.5 rounded-full bg-passed" />
            Agentless Read-Only Mode
          </span>
        </div>
      </header>

      {/* Top Row: Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* ThreatScore */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 flex flex-col justify-between hover:border-primary/40 transition-all shadow-sm hover:shadow-md relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none group-hover:bg-primary/10 transition-colors" />
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-label text-on-surface-variant uppercase tracking-wider font-semibold">
              ThreatScore
            </span>
            <Shield className="w-5 h-5 text-primary" />
          </div>
          <div className="flex items-end gap-3">
            <span className="text-5xl font-headline font-bold text-primary">
              {threatSummary.threat_score}%
            </span>
            <span className="text-xs font-semibold text-passed bg-passed/10 px-2.5 py-1 rounded-full mb-1 border border-passed/20">
              {threatSummary.risk_level}
            </span>
          </div>
        </div>

        {/* Total Findings */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 flex flex-col justify-between hover:border-critical/30 transition-all shadow-sm hover:shadow-md">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-label text-on-surface-variant uppercase tracking-wider font-semibold">
              Total Findings
            </span>
            <AlertTriangle className="w-5 h-5 text-critical" />
          </div>
          <div className="flex items-end gap-3">
            <span className="text-4xl font-headline font-bold text-on-surface">
              {threatSummary.total_findings.toLocaleString()}
            </span>
            <span className="text-xs font-semibold text-critical bg-critical/10 px-2 py-1 rounded mb-1 flex items-center border border-critical/20">
              <TrendingUp className="w-3 h-3 mr-1" />
              {threatSummary.findings_delta}
            </span>
          </div>
        </div>

        {/* Scanned Resources */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 flex flex-col justify-between hover:border-secondary/30 transition-all shadow-sm hover:shadow-md">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-label text-on-surface-variant uppercase tracking-wider font-semibold">
              Scanned Resources
            </span>
            <Cloud className="w-5 h-5 text-secondary" />
          </div>
          <div className="flex items-end gap-3">
            <span className="text-4xl font-headline font-bold text-on-surface">
              {threatSummary.scanned_resources}
            </span>
            <span className="text-xs text-on-surface-variant mb-1 font-label">
              S3, IAM, EC2, CloudTrail
            </span>
          </div>
        </div>

        {/* Active Policies */}
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 flex flex-col justify-between hover:border-high/30 transition-all shadow-sm hover:shadow-md">
          <div className="flex justify-between items-start mb-4">
            <span className="text-xs font-label text-on-surface-variant uppercase tracking-wider font-semibold">
              Active Policies
            </span>
            <FileCheck2 className="w-5 h-5 text-high" />
          </div>
          <div className="flex items-end gap-3">
            <span className="text-4xl font-headline font-bold text-on-surface">
              {threatSummary.active_policies}
            </span>
            <span className="text-xs text-passed mb-1 font-semibold">
              {frameworks.length} Frameworks Active
            </span>
          </div>
        </div>
      </div>

      {/* Middle Grid: Severity Distribution & Compliance Scorecard */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Severity Distribution Chart (8 cols) */}
        <div className="lg:col-span-8 bg-surface border border-outline-variant rounded-2xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-headline font-semibold text-on-surface">
                Findings by Severity
              </h2>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Distribution of misconfigurations across cloud accounts
              </p>
            </div>
            <button
              onClick={() => navigate('/findings')}
              className="text-xs font-label text-primary hover:underline flex items-center gap-1 font-semibold"
            >
              <span>View All Details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Severity Bar Chart */}
          <div className="h-56 flex items-end gap-6 px-4 pb-6 pt-4 border-b border-l border-outline-variant/60 relative">
            {/* Critical */}
            <div className="flex-1 flex flex-col justify-end items-center group">
              <div
                className="w-full max-w-[64px] bg-critical/90 hover:bg-critical rounded-t-md transition-all relative cursor-pointer shadow-[0_0_12px_rgba(239,68,68,0.25)]"
                style={{ height: '28%' }}
              >
                <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-container-highest text-[11px] font-mono font-bold text-on-surface px-2 py-0.5 rounded border border-outline-variant opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {threatSummary.severity_breakdown.critical} Critical
                </div>
              </div>
              <span className="text-xs text-on-surface-variant mt-2 font-label">
                Critical ({threatSummary.severity_breakdown.critical})
              </span>
            </div>

            {/* High */}
            <div className="flex-1 flex flex-col justify-end items-center group">
              <div
                className="w-full max-w-[64px] bg-high/90 hover:bg-high rounded-t-md transition-all relative cursor-pointer shadow-[0_0_12px_rgba(249,115,22,0.25)]"
                style={{ height: '48%' }}
              >
                <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-container-highest text-[11px] font-mono font-bold text-on-surface px-2 py-0.5 rounded border border-outline-variant opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {threatSummary.severity_breakdown.high} High
                </div>
              </div>
              <span className="text-xs text-on-surface-variant mt-2 font-label">
                High ({threatSummary.severity_breakdown.high})
              </span>
            </div>

            {/* Medium */}
            <div className="flex-1 flex flex-col justify-end items-center group">
              <div
                className="w-full max-w-[64px] bg-medium/90 hover:bg-medium rounded-t-md transition-all relative cursor-pointer shadow-[0_0_12px_rgba(234,179,8,0.25)]"
                style={{ height: '82%' }}
              >
                <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-container-highest text-[11px] font-mono font-bold text-on-surface px-2 py-0.5 rounded border border-outline-variant opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {threatSummary.severity_breakdown.medium} Medium
                </div>
              </div>
              <span className="text-xs text-on-surface-variant mt-2 font-label">
                Medium ({threatSummary.severity_breakdown.medium})
              </span>
            </div>

            {/* Low */}
            <div className="flex-1 flex flex-col justify-end items-center group">
              <div
                className="w-full max-w-[64px] bg-low/90 hover:bg-low rounded-t-md transition-all relative cursor-pointer shadow-[0_0_12px_rgba(59,130,246,0.25)]"
                style={{ height: '60%' }}
              >
                <div className="absolute -top-7 left-1/2 -translate-x-1/2 bg-surface-container-highest text-[11px] font-mono font-bold text-on-surface px-2 py-0.5 rounded border border-outline-variant opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {threatSummary.severity_breakdown.low} Low
                </div>
              </div>
              <span className="text-xs text-on-surface-variant mt-2 font-label">
                Low ({threatSummary.severity_breakdown.low})
              </span>
            </div>
          </div>
        </div>

        {/* Compliance Framework Scorecard (4 cols) */}
        <div className="lg:col-span-4 bg-surface border border-outline-variant rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-headline font-semibold text-on-surface">
                Framework Scores
              </h2>
              <button
                onClick={() => navigate('/compliance')}
                className="text-xs font-label text-primary hover:underline font-semibold"
              >
                Matrix
              </button>
            </div>
            <div className="space-y-4">
              {frameworks.slice(0, 3).map((fw) => (
                <div key={fw.id} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-label">
                    <span className="text-on-surface font-medium truncate max-w-[180px]">
                      {fw.name}
                    </span>
                    <span className="text-primary font-mono font-bold">{fw.score}%</span>
                  </div>
                  <div className="w-full bg-surface-container-high h-2 rounded-full overflow-hidden border border-outline-variant">
                    <div
                      className="bg-gradient-to-r from-primary to-secondary h-full rounded-full transition-all duration-500"
                      style={{ width: `${fw.score}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-outline-variant mt-4 flex items-center justify-between text-xs text-on-surface-variant font-label">
            <span>Next Automated Scan:</span>
            <span className="text-on-surface font-mono font-semibold">Today, 23:00 UTC</span>
          </div>
        </div>
      </div>

      {/* Bottom Table: Urgent Action Items */}
      <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-sm">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-lg font-headline font-semibold text-on-surface">
              Urgent Remediation Items
            </h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              Top critical risks requiring immediate architectural or policy fixes
            </p>
          </div>
          <button
            onClick={() => navigate('/findings')}
            className="text-xs font-label text-primary hover:underline flex items-center gap-1 font-semibold"
          >
            <span>Full Explorer</span>
            <ExternalLink className="w-3 h-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 text-on-surface-variant font-semibold text-xs font-label uppercase tracking-wider border-b border-outline-variant">
              <tr>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Rule / Title</th>
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-4">Resource ARN</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/60">
              {criticalAndHigh.map((f) => (
                <tr
                  key={f.id}
                  className="hover:bg-blue-50/40 transition-colors group cursor-pointer"
                  onClick={() => handleViewFix(f)}
                >
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold font-label ${
                        f.severity === 'CRITICAL'
                          ? 'bg-critical/15 text-critical border border-critical/30'
                          : 'bg-high/15 text-high border border-high/30'
                      }`}
                    >
                      {f.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <p className="text-sm font-medium text-on-surface group-hover:text-primary transition-colors">
                      {f.title}
                    </p>
                    <p className="text-xs font-mono text-on-surface-variant/80">
                      {f.rule_id}
                    </p>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono border border-outline-variant text-on-surface font-medium">
                      {f.service_name}
                    </span>
                  </td>
                  <td className="py-3 px-4 max-w-xs truncate font-mono text-xs text-on-surface-variant">
                    {f.resource_arn}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewFix(f);
                      }}
                      className="px-3 py-1 bg-primary/10 text-primary hover:bg-primary hover:text-on-primary rounded text-xs font-label font-semibold border border-primary/30 transition-colors"
                    >
                      View Fix
                    </button>
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

