import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Lock, Eye, EyeOff, Loader2, CheckCircle2, AlertCircle, ArrowLeft, Shield } from 'lucide-react';

export const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryToken = searchParams.get('token') || '';

  const [token, setToken] = useState(queryToken);
  const [manualToken, setManualToken] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Verify token when component mounts or token changes
  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setTokenValid(false);
        setError('No reset token provided. Please use the link sent to your email or enter your token below.');
        return;
      }

      setVerifying(true);
      setError(null);
      try {
        const resp = await api.verifyResetToken(token);
        if (resp.valid) {
          setTokenValid(true);
          setUserEmail(resp.email);
        } else {
          setTokenValid(false);
          setError('This password reset link is invalid or has expired.');
        }
      } catch (err: unknown) {
        setTokenValid(false);
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setError(msg || 'This password reset link is invalid or has expired.');
      } finally {
        setVerifying(false);
      }
    };

    void verify();
  }, [token]);

  // Password requirement checks
  const hasMinLength = newPassword.length >= 12;
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hasMinLength) {
      setError('Password must be at least 12 characters long.');
      return;
    }
    if (!passwordsMatch) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await api.resetPassword({ token, new_password: newPassword });
      setSuccess(true);
      setTimeout(() => {
        navigate('/login', {
          state: { message: 'Password reset successfully! Please sign in with your new password.' },
        });
      }, 2000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Failed to reset password. The link may have expired.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleManualTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualToken.trim()) return;
    setToken(manualToken.trim());
  };

  return (
    <div>
      {/* Brand Icon Header */}
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-md shadow-blue-500/10">
          <Shield className="w-8 h-8 text-primary" />
        </div>
      </div>

      <h1 className="text-2xl font-headline font-bold text-center text-on-surface tracking-tight mb-2">
        Set new password
      </h1>
      <p className="text-on-surface-variant text-center mb-6 text-xs font-label">
        {userEmail
          ? `Create a strong password for ${userEmail}`
          : 'Choose a strong password with at least 12 characters'}
      </p>

      {verifying && (
        <div className="py-8 flex flex-col items-center justify-center space-y-3 text-on-surface-variant">
          <Loader2 className="w-6 h-6 animate-spin text-primary" />
          <p className="text-xs">Verifying reset token...</p>
        </div>
      )}

      {!verifying && tokenValid === false && (
        <div className="space-y-5">
          <div className="p-4 rounded-xl bg-critical/10 border border-critical/20 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-critical shrink-0 mt-0.5" />
            <div className="text-xs space-y-1">
              <p className="font-semibold text-critical">Invalid or Expired Link</p>
              <p className="text-on-surface-variant leading-relaxed">
                {error || 'This password reset link is invalid or has expired. For security, links expire after 1 hour.'}
              </p>
            </div>
          </div>

          {/* Optional manual token entry */}
          <form onSubmit={handleManualTokenSubmit} className="space-y-2">
            <label
              htmlFor="manual-token"
              className="block text-xs font-medium text-on-surface-variant font-label"
            >
              Have a token? Paste it below:
            </label>
            <div className="flex gap-2">
              <input
                id="manual-token"
                type="text"
                value={manualToken}
                onChange={(e) => setManualToken(e.target.value)}
                placeholder="Paste token..."
                className="bg-surface border border-outline-variant text-on-surface text-xs rounded-lg p-2.5 flex-1 focus:ring-1 focus:ring-primary focus:border-primary"
              />
              <button
                type="submit"
                disabled={!manualToken.trim()}
                className="px-3 py-2 bg-primary text-on-primary text-xs rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50"
              >
                Verify
              </button>
            </div>
          </form>

          <div className="pt-2 flex flex-col gap-3">
            <Link
              to="/forgot-password"
              className="w-full flex items-center justify-center py-2.5 px-4 rounded-lg bg-surface border border-outline-variant hover:bg-surface-container-high text-on-surface text-xs font-medium transition-colors"
            >
              Request a New Reset Link
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center text-xs text-on-surface-variant hover:text-on-surface font-label"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
              Return to sign in
            </Link>
          </div>
        </div>
      )}

      {!verifying && tokenValid && !success && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="new-password"
              className="block text-xs font-medium text-on-surface-variant mb-1 font-label"
            >
              New Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="new-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 12 characters"
                className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 pr-10 p-2.5 placeholder-on-surface-variant/40 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-on-surface-variant/60 hover:text-on-surface transition-colors"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label
              htmlFor="confirm-password"
              className="block text-xs font-medium text-on-surface-variant mb-1 font-label"
            >
              Confirm New Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="confirm-password"
                type={showConfirmPassword ? 'text' : 'password'}
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat password"
                className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 pr-10 p-2.5 placeholder-on-surface-variant/40 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-on-surface-variant/60 hover:text-on-surface transition-colors"
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Password Validation Indicators */}
          <div className="p-3 rounded-lg bg-surface-container-low border border-outline-variant text-xs space-y-1.5 font-label">
            <div className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${hasMinLength ? 'bg-passed' : 'bg-outline'}`} />
              <span className={hasMinLength ? 'text-passed font-medium' : 'text-on-surface-variant'}>
                At least 12 characters
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`w-1.5 h-1.5 rounded-full ${passwordsMatch ? 'bg-passed' : 'bg-outline'}`} />
              <span className={passwordsMatch ? 'text-passed font-medium' : 'text-on-surface-variant'}>
                Passwords match
              </span>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-critical/10 border border-critical/20 text-xs text-critical">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || !hasMinLength || !passwordsMatch}
            className="w-full flex items-center justify-center py-2.5 px-4 rounded-lg bg-primary hover:bg-primary/90 text-on-primary text-sm font-medium transition-all shadow-md shadow-blue-500/15 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Updating password...
              </>
            ) : (
              'Save New Password'
            )}
          </button>

          <div className="pt-2 text-center">
            <Link
              to="/login"
              className="inline-flex items-center text-xs font-medium text-primary hover:underline font-label"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
              Cancel and return to sign in
            </Link>
          </div>
        </form>
      )}

      {success && (
        <div className="p-4 rounded-xl bg-passed/10 border border-passed/20 text-center space-y-3">
          <CheckCircle2 className="w-8 h-8 text-passed mx-auto" />
          <h2 className="text-sm font-bold text-passed font-headline">Password Successfully Updated</h2>
          <p className="text-xs text-on-surface-variant">
            Your credentials have been securely updated. Redirecting to sign in...
          </p>
          <div className="pt-2">
            <Link
              to="/login"
              className="inline-block py-2 px-4 rounded-lg bg-primary text-on-primary text-xs font-medium"
            >
              Sign In Now
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
