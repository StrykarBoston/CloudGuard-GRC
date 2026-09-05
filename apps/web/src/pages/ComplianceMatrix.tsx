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
              className="w-full pl-9 pr-3 py-2 bg-surface-container border border-outline-variant/60 rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary placeholder-on-surface-variant/40"
            />
          </div>

          <button
            onClick={handleExportPDF}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary font-label font-semibold rounded-lg text-xs hover:bg-primary-container transition-colors shadow-[0_0_12px_rgba(0,212,255,0.2)]"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{exporting ? 'Generating PDF...' : 'Export Audit PDF'}</span>
          </button>
        </div>
      </div>

      {/* Bento Grid: Framework Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {frameworks.map((fw) => {
          const isSelected = fw.id === selectedFrameworkId;
          return (
            <div
              key={fw.id}
              onClick={() => setSelectedFrameworkId(fw.id)}
              className={`bg-surface-container/60 border rounded-2xl p-5 cursor-pointer transition-all duration-200 relative overflow-hidden shadow-lg flex flex-col justify-between ${
                isSelected
                  ? 'border-primary shadow-[0_0_15px_rgba(0,212,255,0.15)] bg-surface-container-high/60 scale-[1.01]'
                  : 'border-outline-variant/60 hover:border-primary/40'
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
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-container text-on-surface-variant border border-outline-variant/40">
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
              <div className="mt-5 pt-4 border-t border-outline-variant/40 flex items-center justify-between">
                <div>
                  <span className="text-2xl font-headline font-bold text-primary">
                    {fw.score}%
                  </span>
                  <p className="text-[11px] text-on-surface-variant font-label">
                    {fw.passed_controls} / {fw.total_controls} Controls Passed
                  </p>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-label font-medium ${
                    fw.score >= 80
                      ? 'bg-passed/10 text-passed border border-passed/30'
                      : 'bg-high/10 text-high border border-high/30'
                  }`}
                >
                  {fw.score >= 80 ? 'Compliant' : 'Review Required'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Control Level Breakdown Table */}
      {activeFramework && (
        <div className="bg-surface-container/50 backdrop-blur-sm border border-outline-variant/60 rounded-2xl p-6 shadow-lg">
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
              <thead className="bg-surface-container-low text-on-surface-variant font-medium font-label border-b border-outline-variant/50">
                <tr>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Control ID</th>
                  <th className="py-3 px-4">Control Requirement</th>
                  <th className="py-3 px-4">Mapped Detection Rules</th>
                  <th className="py-3 px-4 text-right">Evidence State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/30">
                {activeFramework.controls.map((ctrl) => (
                  <tr key={ctrl.id} className="hover:bg-surface-container-high/40 transition-colors">
                    <td className="py-3.5 px-4">
                      {ctrl.status === 'PASS' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-passed/10 text-passed border border-passed/30 font-semibold font-label text-[11px]">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Pass
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
                            className="px-2 py-0.5 bg-surface-container rounded text-[11px] font-mono border border-outline-variant/40 text-primary"
                          >
                            {r}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-[11px] text-on-surface-variant">
                      {ctrl.status === 'PASS' ? (
                        <span className="text-passed">Verified Clean</span>
                      ) : (
                        <span className="text-critical">Remediation Required</span>
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
