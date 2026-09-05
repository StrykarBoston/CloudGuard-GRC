import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { Shield, Mail, Lock, Building, User as UserIcon, Loader2 } from 'lucide-react';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [company, setCompany] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try { await register(company, fullName, email, password); navigate('/accounts/onboard'); }
    catch { setError('Registration failed. Use a unique email, organization name, and a password with at least 12 characters.'); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div className="flex justify-center mb-6">
        <div className="w-16 h-16 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary shadow-[0_0_20px_rgba(0,212,255,0.25)]">
          <Shield className="w-8 h-8 fill-primary/20 text-primary" />
        </div>
      </div>

      <h1 className="text-2xl font-headline font-bold text-center text-on-surface tracking-tight mb-2">
        Create organization
      </h1>
      <p className="text-on-surface-variant text-center mb-6 text-xs font-label">
        Start continuous read-only cloud compliance monitoring
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
            Full Name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
              <UserIcon className="w-4 h-4" />
            </div>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Alice Vance"
              className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 p-2.5 placeholder-on-surface-variant/40"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
            Company / Organization
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
              <Building className="w-4 h-4" />
            </div>
            <input
              type="text"
              required
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Acme Corp"
              className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 p-2.5 placeholder-on-surface-variant/40"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
            Work Email
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alice@acme.com"
              className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 p-2.5 placeholder-on-surface-variant/40"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-on-surface-variant mb-1 font-label">
            Master Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-on-surface-variant/60">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="bg-surface border border-outline-variant text-on-surface text-sm rounded-lg focus:ring-1 focus:ring-primary focus:border-primary block w-full pl-9 p-2.5 placeholder-on-surface-variant/40"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 text-surface bg-primary hover:bg-primary-container focus:ring-4 focus:outline-none focus:ring-primary/30 font-semibold rounded-lg text-sm px-5 py-3 text-center font-headline transition-all active:scale-[0.98] shadow-[0_0_15px_rgba(0,212,255,0.3)] flex items-center justify-center gap-2"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            'Complete Setup & Connect Cloud'
          )}
        </button>

        {error && <p className="text-xs text-critical">{error}</p>}

        <div className="pt-2 text-center">
          <span className="text-xs text-on-surface-variant font-label">
            Already registered?{' '}
          </span>
          <Link
            to="/login"
            className="text-xs font-medium text-primary hover:underline font-label"
          >
            Sign in to existing tenant
          </Link>
        </div>
      </form>
    </div>
  );
};
