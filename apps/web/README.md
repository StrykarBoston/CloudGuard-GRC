# CloudGuard GRC Web Client

The **CloudGuard GRC Web Client** is a responsive, modern single-page web portal built with **React 18**, **TypeScript**, **Vite**, and **Tailwind CSS**. It provides security analysts, auditors, and administrators with an intuitive interface to monitor cloud posture, inspect findings, manage compliance frameworks, and export executive reports.

---

## 🎨 User Interface & Pages

| Page Route | Component | Purpose |
| :--- | :--- | :--- |
| `/login` | `Login.tsx` | Secure sign-in with show/hide password, error feedback, and lockout alerts |
| `/register` | `Register.tsx` | Organization setup and administrator registration |
| `/forgot-password` | `ForgotPassword.tsx` | Password reset request with local development assistant |
| `/reset-password` | `ResetPassword.tsx` | Token verification, password strength requirements, and reset form |
| `/dashboard` | `Dashboard.tsx` | Threat score gauge, risk level indicator, and severity breakdown |
| `/findings` | `FindingsExplorer.tsx` | Filterable findings table with Terraform & AWS CLI remediation drawer |
| `/compliance` | `ComplianceMatrix.tsx` | Framework posture cards (CIS, GDPR, DPDPA, ISO 27001) and PDF export |
| `/accounts` | `Accounts.tsx` | Inventory of connected AWS accounts and connection status |
| `/accounts/onboard` | `AccountOnboarding.tsx` | Step-by-step AWS STS AssumeRole onboarding wizard with copyable IAM policy |
| `/settings` | `Settings.tsx` | Automated daily scan scheduling and Slack webhook alert configuration |
| `/audit-logs` | `AuditLog.tsx` | Complete immutable audit trail of user actions and security events |

---

## 🛠️ Technology Stack

- **Framework:** React 18 with Vite 6
- **Language:** TypeScript 5.6 (strict mode)
- **Styling:** Tailwind CSS v3 with custom dark slate and royal blue palette
- **State Management:** Zustand (lightweight session and scan state)
- **Server Cache & Data Fetching:** TanStack Query v5
- **Icons:** Lucide React
- **HTTP Client:** Axios with automatic 401 token refresh interceptor

---

## 💻 Local Development

### 1. Install Dependencies
```powershell
npm install
```

### 2. Start Vite Development Server
```powershell
npm run dev
```
The application will be accessible at [http://localhost:5173](http://localhost:5173). Requests to `/api` are automatically proxied to the backend at `http://localhost:8000`.

### 3. Build for Production
```powershell
npm run build
```
Runs TypeScript verification (`tsc -b`) and Vite production bundle generation into the `dist/` directory.

### 4. Code Linting
```powershell
npm run lint
```
