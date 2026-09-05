import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { AuthLayout } from './components/layout/AuthLayout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { FindingsExplorer } from './pages/FindingsExplorer';
import { ComplianceMatrix } from './pages/ComplianceMatrix';
import { Accounts } from './pages/Accounts';
import { AccountOnboarding } from './pages/AccountOnboarding';
import { Settings } from './pages/Settings';
import { useAuthStore } from './store/useAuthStore';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function Protected({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, restore } = useAuthStore();
  useEffect(() => { void restore(); }, [restore]);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Route>

          {/* Protected Application Routes inside AppShell */}
          <Route element={<Protected><AppShell /></Protected>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/findings" element={<FindingsExplorer />} />
            <Route path="/compliance" element={<ComplianceMatrix />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/accounts/onboard" element={<AccountOnboarding />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* Root and Catch-All Redirects */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
export default App;
