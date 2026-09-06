import React, { useState, useMemo } from 'react';
import { useScanStore } from '../store/useScanStore';
import { useFindings, useFindingStatus } from '../hooks/useCloudGuard';
import {
  Search,
  FilterX,
  Download,
  Copy,
  Check,
  X,
  FileCode2,
  Terminal,
  ShieldAlert,
  Loader2,
} from 'lucide-react';

export const FindingsExplorer: React.FC = () => {
  const { selectedFinding, selectFinding } = useScanStore();
  const { data: findings = [], isLoading } = useFindings();
  const { mutate: updateStatus } = useFindingStatus();

  const suppressFinding = (id: string) => {
    updateStatus({ id, status: 'SUPPRESSED' });
    selectFinding(null);
  };
  
  const resolveFinding = (id: string) => {
    updateStatus({ id, status: 'RESOLVED' });
    selectFinding(null);
  };

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedService, setSelectedService] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [copiedTab, setCopiedTab] = useState<string | null>(null);
  const [activeRemediationTab, setActiveRemediationTab] = useState<'terraform' | 'cli'>('terraform');

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      const matchesSearch =
        searchQuery === '' ||
        f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.resource_arn.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.rule_id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSeverity =
        selectedSeverity === 'ALL' || f.severity === selectedSeverity;
      const matchesService =
        selectedService === 'ALL' || f.service_name === selectedService;
      const matchesStatus =
        selectedStatus === 'ALL' || f.status === selectedStatus;

      return matchesSearch && matchesSeverity && matchesService && matchesStatus;
    });
  }, [findings, searchQuery, selectedSeverity, selectedService, selectedStatus]);

  const handleCopyCode = (text: string, tab: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTab(tab);
    setTimeout(() => setCopiedTab(null), 2000);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedSeverity('ALL');
    setSelectedService('ALL');
    setSelectedStatus('ALL');
  };

  return (
    <div className="relative h-[calc(100vh-7rem)] flex flex-col -m-6 md:-m-8 lg:-m-10">
      {/* Header & Filter Controls Toolbar */}
      <div className="px-6 sm:px-8 py-5 border-b border-outline-variant bg-surface shrink-0 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-headline font-bold text-on-surface tracking-tight">
              Findings Explorer
            </h1>
            <p className="text-xs text-on-surface-variant mt-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span>{filteredFindings.length} misconfigurations displayed</span>
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                const csvData =
                  'data:text/csv;charset=utf-8,ID,Rule,Severity,Service,ARN,Status\n' +
                  filteredFindings
                    .map(
                      (f) =>
                        `"${f.id}","${f.rule_id}","${f.severity}","${f.service_name}","${f.resource_arn}","${f.status}"`
                    )
                    .join('\n');
                const encodedUri = encodeURI(csvData);
                const link = document.createElement('a');
                link.setAttribute('href', encodedUri);
                link.setAttribute('download', 'cloudguard_findings.csv');
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
              className="px-3.5 py-2 bg-surface hover:bg-slate-100 text-on-surface text-xs font-label font-medium rounded-lg border border-outline-variant shadow-xs transition-colors flex items-center gap-2"
            >
              <Download className="w-3.5 h-3.5 text-primary" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative flex-1 min-w-[240px] max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search findings, rules, ARNs..."
              className="w-full pl-9 pr-4 py-2 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary placeholder-on-surface-variant/50 shadow-xs"
            />
          </div>

          {/* Severity Dropdown */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="px-3 py-2 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary shadow-xs"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Service Dropdown */}
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="px-3 py-2 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary shadow-xs"
          >
            <option value="ALL">All Services</option>
            <option value="S3">S3</option>
            <option value="IAM">IAM</option>
            <option value="EC2">EC2</option>
            <option value="CloudTrail">CloudTrail</option>
            <option value="KMS">KMS</option>
          </select>

          {/* Status Dropdown */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary shadow-xs"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="RESOLVED">Resolved</option>
            <option value="SUPPRESSED">Suppressed</option>
          </select>

          {(searchQuery ||
            selectedSeverity !== 'ALL' ||
            selectedService !== 'ALL' ||
            selectedStatus !== 'ALL') && (
            <button
              onClick={handleClearFilters}
              className="px-2.5 py-1.5 text-on-surface-variant hover:text-on-surface text-xs flex items-center gap-1 transition-colors"
            >
              <FilterX className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Data Table */}
      <div className="flex-1 overflow-auto bg-surface">
        <table className="w-full text-left text-xs whitespace-nowrap">
          <thead className="bg-slate-50 sticky top-0 z-10 text-on-surface-variant font-semibold font-label text-xs uppercase tracking-wider border-b border-outline-variant">
            <tr>
              <th className="py-3 px-6">Severity</th>
              <th className="py-3 px-4">Rule ID / Title</th>
              <th className="py-3 px-4">Service</th>
              <th className="py-3 px-4">Resource Identifier</th>
              <th className="py-3 px-4">GRC Controls</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-6 text-right">Remediation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant/60">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-16 text-center text-on-surface-variant flex justify-center">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </td>
              </tr>
            ) : filteredFindings.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-16 text-center text-on-surface-variant">
                  No matching findings detected for the selected filters.
                </td>
              </tr>
            ) : (
              filteredFindings.map((finding) => (
                <tr
                  key={finding.id}
                  onClick={() => selectFinding(finding)}
                  className={`hover:bg-blue-50/50 transition-colors cursor-pointer ${
                    selectedFinding?.id === finding.id ? 'bg-blue-50/80' : ''
                  }`}
                >
                  <td className="py-3.5 px-6">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold font-label ${
                        finding.severity === 'CRITICAL'
                          ? 'bg-critical/15 text-critical border border-critical/30'
                          : finding.severity === 'HIGH'
                          ? 'bg-high/15 text-high border border-high/30'
                          : finding.severity === 'MEDIUM'
                          ? 'bg-medium/15 text-medium border border-medium/30'
                          : 'bg-low/15 text-low border border-low/30'
                      }`}
                    >
                      {finding.severity}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <p className="text-sm font-medium text-on-surface">{finding.title}</p>
                    <p className="font-mono text-xs text-on-surface-variant/70">
                      {finding.rule_id}
                    </p>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-xs font-mono border border-outline-variant text-on-surface font-medium">
                      {finding.service_name}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 max-w-xs truncate font-mono text-xs text-on-surface-variant">
                    {finding.resource_arn}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex gap-1.5 flex-wrap max-w-xs">
                      {finding.compliance_controls.map((ctrl) => (
                        <span
                          key={ctrl}
                          className="px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20 text-[10px] font-mono"
                        >
                          {ctrl}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-label font-medium ${
                        finding.status === 'OPEN'
                          ? 'bg-error/10 text-error'
                          : finding.status === 'RESOLVED'
                          ? 'bg-passed/10 text-passed'
                          : 'bg-outline/20 text-on-surface-variant'
                      }`}
                    >
                      {finding.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        selectFinding(finding);
                      }}
                      className="px-3 py-1 bg-primary/10 text-primary hover:bg-primary hover:text-on-primary rounded text-xs font-label font-semibold border border-primary/30 transition-colors"
                    >
                      View Fix
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Slide-over Finding Detail Drawer */}
      {selectedFinding && (
        <div className="fixed inset-y-0 right-0 z-40 w-full sm:max-w-2xl bg-surface border-l border-outline-variant shadow-2xl flex flex-col">
          {/* Drawer Header */}
          <div className="p-6 border-b border-outline-variant flex items-start justify-between bg-slate-50/80">
            <div className="pr-4">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold font-label ${
                    selectedFinding.severity === 'CRITICAL'
                      ? 'bg-critical/20 text-critical border border-critical/30'
                      : 'bg-high/20 text-high border border-high/30'
                  }`}
                >
                  {selectedFinding.severity}
                </span>
                <span className="text-xs font-mono text-on-surface-variant">
                  {selectedFinding.rule_id}
                </span>
              </div>
              <h2 className="text-xl font-headline font-bold text-on-surface">
                {selectedFinding.title}
              </h2>
            </div>
            <button
              onClick={() => selectFinding(null)}
              className="text-on-surface-variant hover:text-on-surface p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Impact Box */}
            <div className="bg-blue-50/60 border border-blue-100 rounded-xl p-4">
              <h4 className="text-xs font-label uppercase text-primary tracking-wider font-semibold mb-1">
                Security Impact & Exposure
              </h4>
              <p className="text-sm text-on-surface leading-relaxed">
                {selectedFinding.impact || selectedFinding.description}
              </p>
            </div>

            {/* Resource ARN */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <span className="text-xs font-label uppercase text-on-surface-variant tracking-wider font-semibold">
                  Affected AWS Resource ARN
                </span>
                <button
                  onClick={() =>
                    handleCopyCode(selectedFinding.resource_arn, 'arn')
                  }
                  className="text-xs text-primary hover:underline flex items-center gap-1"
                >
                  {copiedTab === 'arn' ? (
                    <Check className="w-3.5 h-3.5 text-passed" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  <span>Copy ARN</span>
                </button>
              </div>
              <div className="bg-slate-50 border border-outline-variant rounded-lg p-3 font-mono text-xs text-slate-800 break-all select-all">
                {selectedFinding.resource_arn}
              </div>
            </div>

            {/* Compliance Mapping */}
            <div>
              <span className="text-xs font-label uppercase text-on-surface-variant tracking-wider font-semibold block mb-2">
                Mapped GRC Framework Controls
              </span>
              <div className="flex gap-2 flex-wrap">
                {selectedFinding.compliance_controls.map((ctrl) => (
                  <span
                    key={ctrl}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-blue-50 text-blue-800 border border-blue-200 text-xs font-mono font-medium"
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-primary" />
                    {ctrl}
                  </span>
                ))}
              </div>
            </div>

            {/* Remediation Tabs */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-label uppercase text-on-surface-variant tracking-wider font-semibold">
                  Remediation Code Fixes
                </span>
                <div className="flex bg-slate-100 rounded-lg p-0.5 border border-outline-variant">
                  <button
                    onClick={() => setActiveRemediationTab('terraform')}
                    className={`flex items-center gap-1.5 px-3 py-1 text-xs font-label font-medium rounded-md transition-all ${
                      activeRemediationTab === 'terraform'
                        ? 'bg-primary text-on-primary shadow-xs font-semibold'
                        : 'text-on-surface-variant hover:text-on-surface'
                    }`}
                  >
                    <FileCode2 className="w-3.5 h-3.5" />
                    <span>Terraform</span>
                  </button>
                  <button
                    onClick={() => setActiveRemediationTab('cli')}
                    className={`flex items-center gap-1.5 px-3 py-1 text-xs font-label font-medium rounded-md transition-all ${
                      activeRemediationTab === 'cli'
                        ? 'bg-primary text-on-primary shadow-xs font-semibold'
                        : 'text-on-surface-variant hover:text-on-surface'
                    }`}
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    <span>AWS CLI</span>
                  </button>
                </div>
              </div>

              {/* Code Viewer Container */}
              <div className="relative bg-slate-900 border border-slate-700/80 rounded-xl overflow-hidden shadow-sm">
                <div className="flex justify-between items-center px-4 py-2.5 bg-slate-800 border-b border-slate-700 text-xs font-mono text-slate-300">
                  <span className="font-semibold text-slate-200">
                    {activeRemediationTab === 'terraform' ? 'main.tf' : 'remediate.sh'}
                  </span>
                  <button
                    onClick={() =>
                      handleCopyCode(
                        activeRemediationTab === 'terraform'
                          ? selectedFinding.remediation_json.terraform
                          : selectedFinding.remediation_json.cli,
                        activeRemediationTab
                      )
                    }
                    className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-sans text-xs transition-colors"
                  >
                    {copiedTab === activeRemediationTab ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400 font-medium">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Code</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="p-4 text-xs font-mono text-slate-100 overflow-x-auto leading-relaxed selection:bg-blue-600 selection:text-white">
                  <code>
                    {activeRemediationTab === 'terraform'
                      ? selectedFinding.remediation_json.terraform
                      : selectedFinding.remediation_json.cli}
                  </code>
                </pre>
              </div>
            </div>
          </div>

          {/* Drawer Actions Footer */}
          <div className="p-5 border-t border-outline-variant bg-slate-50 flex items-center justify-between gap-3">
            <button
              onClick={() => suppressFinding(selectedFinding.id)}
              className="px-4 py-2 bg-surface hover:bg-slate-100 border border-outline-variant text-on-surface-variant hover:text-on-surface rounded-lg text-xs font-label font-medium shadow-xs transition-colors"
            >
              Mark as Suppressed
            </button>
            <button
              onClick={() => resolveFinding(selectedFinding.id)}
              className="px-4 py-2 bg-passed/15 hover:bg-passed/25 border border-passed/30 text-passed rounded-lg text-xs font-label font-semibold shadow-xs transition-colors"
            >
              Mark as Resolved
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
