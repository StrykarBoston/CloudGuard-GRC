import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { Shield, Mail, Lock, Eye, EyeOff, Loader2, CheckCircle2 } from 'lucide-react';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Success message passed from reset password flow
  const successMessage = (location.state as { message?: string } | null)?.message;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email.trim().toLowerCase(), password, rememberMe);
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Sign-in failed. Please verify your email and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Brand Icon Header */}
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-md shadow-blue-500/10">
          <Shield className="w-8 h-8 fill-primary/20 text-primary" />
        </div>
      </div>

      <h1 className="text-2xl font-headline font-bold text-center text-on-surface tracking-tight mb-2">
        Welcome back
      </h1>
      <p className="text-on-surface-variant text-center mb-6 text-xs font-label">
        Sign in to access your CloudGuard GRC dashboard
      </p>

      {/* Success alert from password reset or other actions */}
      {successMessage && !error && (
        <div className="mb-5 p-3 rounded-lg bg-passed/10 border border-passed/20 flex items-center gap-2 text-xs text-passed font-medium">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="block text-xs font-medium text-on-surface-variant mb-1.5 font-label"
          >
            Email address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
              <Mail className="w-4 h-4" />
            </div>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 p-2.5 placeholder-on-surface-variant/40 transition-colors"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label
              htmlFor="password"
              className="block text-xs font-medium text-on-surface-variant font-label"
            >
              Password
            </label>
            <Link
              to="/forgot-password"
              className="text-xs font-medium text-primary hover:underline font-label transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
              <Lock className="w-4 h-4" />
            </div>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
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

        {error && (
          <div className="p-3 rounded-lg bg-critical/10 border border-critical/20 text-xs text-critical">
            {error}
          </div>
        )}

        <div className="flex items-center">
          <input
            id="remember"
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            className="w-4 h-4 border border-outline rounded bg-surface text-primary focus:ring-primary/40 accent-primary"
          />
          <label
            htmlFor="remember"
            className="ml-2 text-xs font-medium text-on-surface-variant font-label"
          >
            Remember me for 30 days
          </label>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full text-on-primary bg-primary hover:bg-primary-container focus:ring-4 focus:outline-none focus:ring-primary/30 font-semibold rounded-lg text-sm px-5 py-3 text-center font-headline transition-all active:scale-[0.98] shadow-md shadow-blue-500/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            'Sign in to CloudGuard'
          )}
        </button>

        <div className="pt-2 text-center">
          <span className="text-xs text-on-surface-variant font-label">
            New to CloudGuard?{' '}
          </span>
          <Link
            to="/register"
            className="text-xs font-medium text-primary hover:underline font-label"
          >
            Create an organization
          </Link>
        </div>
      </form>
    </div>
  );
};
