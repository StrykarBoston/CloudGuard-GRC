import React, { useState } from 'react';
import { useCompliance } from '../hooks/useCloudGuard';
import {
  FileCheck2,
  Search,
  Download,
  Shield,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react';

import { api } from '../services/api';

export const ComplianceMatrix: React.FC = () => {
  const { data: frameworks = [], isLoading } = useCompliance();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFrameworkId, setSelectedFrameworkId] = useState<string>(frameworks[0]?.id || '');
  const [exporting, setExporting] = useState(false);

  const activeFramework =
    frameworks.find((f) => f.id === selectedFrameworkId) || frameworks[0];

  const normalizedSearch = searchQuery.trim().toLowerCase();
  const visibleFrameworks = frameworks.filter((framework) => {
    if (!normalizedSearch) return true;
    return framework.name.toLowerCase().includes(normalizedSearch)
      || framework.version.toLowerCase().includes(normalizedSearch)
      || framework.controls.some((control) =>
        `${control.control_id} ${control.title} ${control.description}`.toLowerCase().includes(normalizedSearch)
      );
  });

  if (isLoading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
  }

  const handleExportPDF = async () => {
    if (!activeFramework) return;
    setExporting(true);
    try {
      const blob = await api.exportReport(activeFramework.id);
      const url = window.URL.createObjectURL(new Blob([blob], { type: 'text/html' }));
      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.focus();
      } else {
        const link = document.createElement('a');
        link.href = url;
        link.download = `cloudguard_audit_report_${activeFramework.id}.html`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch {
      alert('Unable to generate executive audit report. Please ensure the backend is connected.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-headline font-bold text-on-surface tracking-tight">
            Compliance Matrix
          </h1>
          <p className="text-on-surface-variant text-sm mt-1 flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-primary" />
            <span>
              Continuous audit evidence mapping across {frameworks.length} active statutory & industry benchmarks.
            </span>
          </p>
          <p className="text-xs text-medium mt-3 max-w-3xl">
            Scores are technical posture scores based on available scan evidence. They are not official compliance certifications or audit opinions.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search frameworks & controls..."
              className="w-full pl-9 pr-3 py-2 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary placeholder-on-surface-variant/40 shadow-xs"
            />
          </div>

          <button
            onClick={handleExportPDF}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary font-label font-semibold rounded-lg text-xs hover:bg-primary-container transition-colors shadow-sm shadow-blue-500/20"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exporting ? 'Generating PDF...' : 'Export Audit PDF'}</span>
          </button>
        </div>
      </div>

      {/* Bento Grid: Framework Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {visibleFrameworks.map((fw) => {
          const isSelected = fw.id === selectedFrameworkId;
          return (
            <div
              key={fw.id}
              onClick={() => setSelectedFrameworkId(fw.id)}
              className={`bg-surface border rounded-2xl p-5 cursor-pointer transition-all duration-200 relative overflow-hidden shadow-xs hover:shadow-md flex flex-col justify-between ${
                isSelected
                  ? 'border-primary ring-2 ring-primary/20 bg-blue-50/25 shadow-md scale-[1.01]'
                  : 'border-outline-variant hover:border-primary/50'
              }`}
            >
              {/* Top accent glow line */}
              <div
                className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${
                  isSelected ? 'from-primary via-secondary to-primary' : 'from-transparent'
                }`}
              />

              <div>
                <div className="flex justify-between items-start mb-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                    <Shield className="w-5 h-5" />
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-on-surface-variant border border-outline-variant">
                    {fw.version}
                  </span>
                </div>

                <h3 className="text-base font-headline font-bold text-on-surface leading-snug">
                  {fw.name}
                </h3>
                <p className="text-xs text-on-surface-variant mt-1 line-clamp-2">
                  {fw.description}
                </p>
              </div>

              {/* Progress Metric */}
              <div className="mt-5 pt-4 border-t border-outline-variant/60 flex items-center justify-between">
                <div>
                  <span className="text-2xl font-headline font-bold text-primary">
                    {fw.score}%
                  </span>
                  <p className="text-[11px] text-on-surface-variant font-label">
                    {fw.passed_controls} / {fw.total_controls} Controls Passed
                  </p>
                </div>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-label font-medium ${
                    fw.score >= 80
                      ? 'bg-passed/10 text-passed border border-passed/30'
                      : 'bg-high/10 text-high border border-high/30'
                  }`}
                >
                  {fw.score >= 80 ? 'Strong Posture' : 'Review Required'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Control Level Breakdown Table */}
      {activeFramework && (
        <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-xl font-headline font-bold text-on-surface">
                {activeFramework.name} Control Breakdown
              </h2>
              <p className="text-xs text-on-surface-variant mt-0.5">
                Detailed audit verification for individual statutory controls
              </p>
            </div>
            <span className="text-xs font-mono text-primary bg-primary/10 px-3 py-1 rounded-md border border-primary/20">
              Selected: {activeFramework.version}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs whitespace-nowrap">
              <thead className="bg-slate-50 text-on-surface-variant font-semibold font-label text-xs uppercase tracking-wider border-b border-outline-variant">
                <tr>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Control ID</th>
                  <th className="py-3 px-4">Control Requirement</th>
                  <th className="py-3 px-4">Mapped Detection Rules</th>
                  <th className="py-3 px-4 text-right">Evidence State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/60">
                {activeFramework.controls.map((ctrl) => (
                  <tr key={ctrl.id} className="hover:bg-blue-50/40 transition-colors">
                    <td className="py-3.5 px-4">
                      {ctrl.status === 'PASS' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-passed/10 text-passed border border-passed/30 font-semibold font-label text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Pass
                        </span>
                      ) : ctrl.status === 'NEEDS_REVIEW' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-medium/10 text-medium border border-medium/30 font-semibold font-label text-[11px]">
                          Review
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-critical/10 text-critical border border-critical/30 font-semibold font-label text-[11px]">
                          <XCircle className="w-3.5 h-3.5" /> Fail
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-on-surface">
                      {ctrl.control_id}
                    </td>
                    <td className="py-3.5 px-4 max-w-md">
                      <p className="text-sm font-medium text-on-surface">{ctrl.title}</p>
                      <p className="text-xs text-on-surface-variant/70 mt-0.5 whitespace-normal">
                        {ctrl.description}
                      </p>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex gap-1.5 flex-wrap">
                        {ctrl.mapped_rules.map((r) => (
                          <span
                            key={r}
                            className="px-2 py-0.5 bg-blue-50 rounded text-[11px] font-mono border border-blue-200 text-primary font-semibold"
                          >
                            {r}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-[11px] text-on-surface-variant">
                      {ctrl.status === 'PASS' ? (
                        <span className="text-passed font-medium">Verified Clean</span>
                      ) : ctrl.status === 'NEEDS_REVIEW' ? (
                        <span className="text-medium font-medium">Evidence Required</span>
                      ) : (
                        <span className="text-critical font-medium">Remediation Required</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
