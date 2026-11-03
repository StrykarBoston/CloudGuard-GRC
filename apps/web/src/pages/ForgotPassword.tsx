import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { KeyRound, Mail, ArrowLeft, Loader2, CheckCircle2, ShieldCheck, ExternalLink } from 'lucide-react';

export const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    setError(null);

    try {
      const resp = await api.forgotPassword(email.trim().toLowerCase());
      setSubmitted(true);
      if (resp.reset_token) {
        setResetToken(resp.reset_token);
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Unable to process your request. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Brand Icon Header */}
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-md shadow-blue-500/10">
          <KeyRound className="w-8 h-8 text-primary" />
        </div>
      </div>

      <h1 className="text-2xl font-headline font-bold text-center text-on-surface tracking-tight mb-2">
        {submitted ? 'Reset instructions generated' : 'Forgot password?'}
      </h1>
      <p className="text-on-surface-variant text-center mb-8 text-xs font-label">
        {submitted
          ? 'Follow the steps below to securely reset your credentials'
          : 'Enter your registered email address to receive password reset instructions'}
      </p>

      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="email"
              className="block text-xs font-medium text-on-surface-variant mb-1.5 font-label"
            >
              Account Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="email"
                type="email"
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 p-2.5 placeholder-on-surface-variant/40 transition-colors"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-critical/10 border border-critical/20 text-xs text-critical">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center py-2.5 px-4 rounded-lg bg-primary hover:bg-primary/90 text-on-primary text-sm font-medium transition-all shadow-md shadow-blue-500/15 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processing request...
              </>
            ) : (
              'Send Reset Instructions'
            )}
          </button>

          <div className="pt-2 text-center">
            <Link
              to="/login"
              className="inline-flex items-center text-xs font-medium text-primary hover:underline font-label"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
              Back to sign in
            </Link>
          </div>
        </form>
      ) : (
        <div className="space-y-5">
          <div className="p-4 rounded-xl bg-passed/10 border border-passed/20 text-xs text-on-surface space-y-2">
            <div className="flex items-center gap-2 text-passed font-medium">
              <CheckCircle2 className="w-4 h-4" />
              <span>Request Processed</span>
            </div>
            <p className="text-on-surface-variant leading-relaxed">
              If an active account exists for <strong className="text-on-surface">{email}</strong>, a secure password reset link has been dispatched.
            </p>
          </div>

          {resetToken && (
            <div className="p-4 rounded-xl bg-primary/10 border border-primary/20 space-y-3">
              <div className="flex items-center gap-2 text-primary font-medium text-xs">
                <ShieldCheck className="w-4 h-4" />
                <span>Instant Reset (Local Verification Active)</span>
              </div>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                For local development and testing, you can proceed directly to choose your new password:
              </p>
              <button
                type="button"
                onClick={() => navigate(`/reset-password?token=${encodeURIComponent(resetToken)}`)}
                className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-primary hover:bg-primary/90 text-on-primary text-xs font-medium transition-colors shadow"
              >
                <span>Reset Password Now</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() => {
                setSubmitted(false);
                setResetToken(null);
              }}
              className="text-xs text-on-surface-variant hover:text-on-surface font-label transition-colors"
            >
              Try another email
            </button>
            <Link
              to="/login"
              className="inline-flex items-center text-xs font-medium text-primary hover:underline font-label"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
              Back to sign in
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

