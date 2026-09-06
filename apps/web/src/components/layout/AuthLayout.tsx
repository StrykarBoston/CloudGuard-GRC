import React from 'react';
import { Outlet } from 'react-router-dom';
import { Shield, Lock } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="font-body text-on-surface min-h-screen flex flex-col justify-between relative bg-background overflow-hidden">
      {/* Background Soft Blue Ambient Glow */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-transparent pointer-events-none rounded-full blur-[140px] opacity-70 w-3/4 mx-auto top-[-20%]" />

      <main className="flex-grow flex items-center justify-center p-6 relative z-10">
        <div className="w-full max-w-md bg-surface border border-outline-variant rounded-2xl shadow-xl overflow-hidden relative">
          {/* Top royal blue accent line */}
          <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-primary/40 via-primary to-primary/40" />

          {/* Child auth form */}
          <div className="p-8 sm:p-10">
            <Outlet />
          </div>

          {/* Security & Compliance Footer Strip */}
          <div className="bg-surface-container-low px-8 py-3.5 border-t border-outline-variant flex justify-center items-center space-x-4 text-xs text-on-surface-variant font-label">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-primary" /> SOC2 Type II Verified
            </span>
            <span className="w-1 h-1 rounded-full bg-outline" />
            <span className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-passed" /> Read-Only STS Assumed
            </span>
          </div>
        </div>
      </main>

      {/* Global Footer */}
      <footer className="bg-surface border-t border-outline-variant font-label text-xs w-full py-6 px-8 flex flex-col md:flex-row justify-between items-center gap-4 relative z-10 text-on-surface-variant">
        <p>© 2026 CloudGuard GRC Enterprise. All rights reserved.</p>
        <ul className="flex flex-wrap items-center justify-center gap-6">
          <li>
            <a href="#" className="hover:text-primary hover:underline transition-colors">
              Privacy Policy
            </a>
          </li>
          <li>
            <a href="#" className="hover:text-primary hover:underline transition-colors">
              Terms of Service
            </a>
          </li>
          <li>
            <a href="#" className="hover:text-primary hover:underline transition-colors">
              Security Compliance
            </a>
          </li>
          <li>
            <a href="#" className="hover:text-primary hover:underline transition-colors">
              Trust Center
            </a>
          </li>
        </ul>
      </footer>
    </div>
  );
};
