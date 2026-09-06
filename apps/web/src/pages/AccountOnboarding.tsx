import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOnboard, useStartScan } from '../hooks/useCloudGuard';
import {
  Copy,
  Check,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
} from 'lucide-react';

export const AccountOnboarding: React.FC = () => {
  const navigate = useNavigate();
  const onboard = useOnboard();
  const startScan = useStartScan();
  const [copied, setCopied] = useState(false);
  const [externalId] = useState(`cg-ext-${Math.random().toString(36).substring(2, 12)}`);
  const [roleArn, setRoleArn] = useState('');
  const [alias, setAlias] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCopyExternalId = () => {
    navigator.clipboard.writeText(externalId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleVerifyAndConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!roleArn.startsWith('arn:aws:iam::')) {
      setError('Please provide a valid AWS IAM Role ARN (format: arn:aws:iam::<account-id>:role/<name>)');
      return;
    }

    setVerifying(true);
    try {
      const account = await onboard.mutateAsync({ account_alias: alias, account_number: accountNumber, role_arn: roleArn, external_id: externalId, validation_mode: 'local_mock' });
      await startScan.mutateAsync(account.id);
      setSuccess(true);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Connection validation failed.');
    } finally { setVerifying(false); }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-headline font-bold text-on-surface tracking-tight">
          Connect Cloud Account
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Add an AWS account via secure, agentless STS AssumeRole with External ID verification.
        </p>
      </div>

      {success ? (
        <div className="bg-surface border border-passed/30 rounded-2xl p-8 text-center space-y-4 shadow-lg">
          <div className="w-14 h-14 bg-passed/10 rounded-full flex items-center justify-center mx-auto text-passed border border-passed/30">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-headline font-bold text-on-surface">
            AWS Account Connected Successfully!
          </h2>
          <p className="text-xs text-on-surface-variant max-w-md mx-auto">
            Local simulated sts:AssumeRole validation succeeded. A read-only baseline scan is running.
          </p>
          <div className="pt-4 flex justify-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-5 py-2.5 bg-primary text-on-primary font-semibold text-xs font-label rounded-lg hover:bg-primary-container transition-all flex items-center gap-2 shadow-sm shadow-blue-500/20"
            >
              <span>Return to Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleVerifyAndConnect} className="space-y-6">
          {/* Step 1: Provider selection */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-xs space-y-4">
            <span className="text-xs font-label uppercase text-on-surface-variant tracking-wider font-semibold">
              Step 1: Select Cloud Provider
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="border-2 border-primary bg-blue-50/60 rounded-xl p-4 flex items-center gap-3 cursor-pointer shadow-xs">
                <span className="text-primary font-headline font-bold text-sm">AWS</span>
                <span className="text-[10px] text-passed bg-passed/10 px-2 py-0.5 rounded font-semibold ml-auto">
                  Supported
                </span>
              </div>
              <div className="border border-outline-variant/60 bg-slate-50 rounded-xl p-4 flex items-center gap-3 opacity-50 cursor-not-allowed">
                <span className="text-on-surface font-headline font-medium text-sm">Azure</span>
                <span className="text-[10px] text-on-surface-variant bg-surface px-2 py-0.5 rounded border border-outline-variant ml-auto">
                  v2 Scope
                </span>
              </div>
              <div className="border border-outline-variant/60 bg-slate-50 rounded-xl p-4 flex items-center gap-3 opacity-50 cursor-not-allowed">
                <span className="text-on-surface font-headline font-medium text-sm">GCP</span>
                <span className="text-[10px] text-on-surface-variant bg-surface px-2 py-0.5 rounded border border-outline-variant ml-auto">
                  v2 Scope
                </span>
              </div>
            </div>
          </div>

          {/* Step 2: External ID */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-xs space-y-3">
            <span className="text-xs font-label uppercase text-on-surface-variant tracking-wider font-semibold">
              Step 2: Generate Confused Deputy External ID
            </span>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              Use this unique string in your IAM Role trust policy condition (`sts:ExternalId`). This local build validates it with a safe simulator and never contacts AWS.
            </p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-slate-50 border border-outline-variant rounded-lg p-3 font-mono text-xs text-primary font-bold">
                {externalId}
              </div>
              <button
                type="button"
                onClick={handleCopyExternalId}
                className="px-4 py-3 bg-surface hover:bg-slate-100 border border-outline-variant text-on-surface text-xs font-label font-medium rounded-lg transition-colors flex items-center gap-1.5 shadow-xs"
              >
                {copied ? <Check className="w-4 h-4 text-passed" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied!' : 'Copy ID'}</span>
              </button>
            </div>
          </div>

          {/* Step 3: Role ARN & Alias */}
          <div className="bg-surface border border-outline-variant rounded-2xl p-6 shadow-xs space-y-4">
            <span className="text-xs font-label uppercase text-on-surface-variant tracking-wider font-semibold">
              Step 3: Provide Read-Only IAM Role Details
            </span>

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
                Account Alias (Display Name)
              </label>
              <input
                type="text"
                required
                value={alias}
                onChange={(e) => setAlias(e.target.value)}
                placeholder="Production-AWS (Primary)"
                className="w-full p-2.5 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
                AWS 12-Digit Account ID
              </label>
              <input
                type="text"
                required
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                placeholder="123456789012"
                className="w-full p-2.5 bg-surface border border-outline-variant rounded-lg text-xs text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
                Read-Only IAM Role ARN
              </label>
              <input
                type="text"
                required
                value={roleArn}
                onChange={(e) => setRoleArn(e.target.value)}
                placeholder="arn:aws:iam::123456789012:role/CloudGuardReadOnlyAuditRole"
                className="w-full p-2.5 bg-surface border border-outline-variant rounded-lg text-xs font-mono text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs"
              />
            </div>

            {error && (
              <div className="p-3 bg-critical/10 border border-critical/30 rounded-lg text-xs text-critical flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={verifying}
            className="w-full py-3 bg-primary hover:bg-primary-container text-on-primary font-headline font-bold rounded-xl text-sm transition-all shadow-md shadow-blue-500/25 flex items-center justify-center gap-2 active:scale-[0.99]"
          >
            {verifying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Testing sts:AssumeRole connection...</span>
              </>
            ) : (
              <span>Verify & Connect Account</span>
            )}
          </button>
        </form>
      )}
    </div>
  );
};
