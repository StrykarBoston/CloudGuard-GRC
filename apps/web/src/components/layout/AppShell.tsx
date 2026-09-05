import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/useAuthStore';
import { useAccounts, useScans, useStartScan } from '../../hooks/useCloudGuard';
import {
  Shield,
  LayoutDashboard,
  AlertTriangle,
  FileCheck2,
  Cloud,
  Settings,
  Bell,
  LogOut,
  Play,
  Loader2,
  Menu,
  X,
  HelpCircle,
} from 'lucide-react';

export const AppShell: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  
  const { data: accounts = [] } = useAccounts();
  const { data: scans = [] } = useScans();
  const { mutate: startScan, isPending } = useStartScan();

  const activeScan = scans.find(s => s.status === 'running' || s.status === 'queued');
  const isScanning = !!activeScan || isPending;
  const scanProgress = activeScan?.progress || 0;

  const handleTriggerScan = () => {
    if (accounts.length > 0) {
      startScan(accounts[0].id);
    }
  };
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Findings', to: '/findings', icon: AlertTriangle },
    { label: 'Compliance', to: '/compliance', icon: FileCheck2 },
    { label: 'Accounts', to: '/accounts', icon: Cloud },
    { label: 'Settings', to: '/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-background text-on-surface flex font-body antialiased">
      {/* Desktop SideNavBar */}
      <aside className="hidden md:flex flex-col h-screen w-64 fixed left-0 top-0 bg-surface-container-lowest border-r border-outline-variant/60 shadow-2xl z-30">
        {/* Brand Header */}
        <div className="p-6 border-b border-outline-variant/30 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center text-primary shadow-[0_0_12px_rgba(0,212,255,0.2)]">
            <Shield className="w-5 h-5 fill-primary/20 text-primary" />
          </div>
          <div>
            <span className="text-lg font-headline font-bold text-primary tracking-tight block">
              CloudGuard GRC
            </span>
            <span className="text-[11px] text-on-surface-variant font-label tracking-wider uppercase">
              Enterprise Security
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg font-label text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-secondary-container text-on-secondary-container font-semibold shadow-inner border border-primary/20 scale-[0.98]'
                      : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-outline-variant/40 bg-surface-container-low/30">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-primary-container/20 border border-primary/30 flex items-center justify-center text-primary font-bold text-xs">
              {user?.full_name?.slice(0, 2).toUpperCase() || 'AD'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-on-surface truncate">
                {user?.full_name || 'Admin User'}
              </p>
              <p className="text-xs text-on-surface-variant truncate">
                {user?.email || 'admin@cloudguard.io'}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="relative w-64 bg-surface-container-lowest border-r border-outline-variant p-6 flex flex-col h-full z-10">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2 text-primary font-headline font-bold text-lg">
                <Shield className="w-5 h-5" /> CloudGuard
              </div>
              <button
                onClick={() => setMobileNavOpen(false)}
                className="text-on-surface-variant hover:text-on-surface p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="flex-1 space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setMobileNavOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg text-sm ${
                        isActive
                          ? 'bg-secondary-container text-on-secondary-container font-semibold'
                          : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
            <button
              onClick={handleLogout}
              className="mt-auto flex items-center gap-2 text-error text-sm py-2"
            >
              <LogOut className="w-4 h-4" /> Logout
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:ml-64 min-h-screen">
        {/* TopNavBar */}
        <header className="sticky top-0 z-20 h-16 bg-surface/85 backdrop-blur-md border-b border-outline-variant/60 px-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileNavOpen(true)}
              className="md:hidden text-on-surface-variant hover:text-on-surface p-1.5 rounded-lg border border-outline-variant"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs font-label bg-surface-container px-3 py-1.5 rounded-full border border-outline-variant/40">
              <span className="w-2 h-2 rounded-full bg-passed animate-pulse" />
              <span className="text-on-surface-variant">Active Target:</span>
              <span className="text-on-surface font-medium">
                {accounts[0]?.account_alias || 'Production-AWS'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 md:gap-4">
            {/* Live Scan Trigger */}
            <button
              onClick={handleTriggerScan}
              disabled={isScanning || accounts.length === 0}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-label font-semibold transition-all shadow-[0_0_12px_rgba(0,212,255,0.15)] ${
                isScanning || accounts.length === 0
                  ? 'bg-surface-container text-primary border border-primary/40 cursor-not-allowed'
                  : 'bg-primary text-on-primary hover:bg-primary-container active:scale-95'
              }`}
            >
              {isScanning ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Scanning ({scanProgress}%)...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run On-Demand Scan</span>
                </>
              )}
            </button>

            <button
              title="Notifications"
              className="text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high p-2 rounded-lg transition-colors"
            >
              <Bell className="w-4 h-4" />
            </button>

            <button
              title="Help & Support"
              className="text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high p-2 rounded-lg transition-colors hidden sm:block"
            >
              <HelpCircle className="w-4 h-4" />
            </button>

            <div className="h-5 w-px bg-outline-variant/60 hidden sm:block" />

            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 text-xs font-label text-on-surface-variant hover:text-error px-2.5 py-1.5 rounded-lg hover:bg-error/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>

        {/* Scan Progress Bar Indicator */}
        {isScanning && (
          <div className="w-full bg-surface-container-low h-1 overflow-hidden">
            <div
              className="bg-primary h-full transition-all duration-300 shadow-[0_0_8px_#00D4FF]"
              style={{ width: `${scanProgress}%` }}
            />
          </div>
        )}

        {/* Outlet for Sub-Routes */}
        <main className="flex-1 p-6 md:p-8 lg:p-10 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

