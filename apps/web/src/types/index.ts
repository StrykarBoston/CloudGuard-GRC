export type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type FindingStatus = 'OPEN' | 'RESOLVED' | 'SUPPRESSED';

export interface RemediationPayload {
  cli: string;
  terraform: string;
  explanation?: string;
}

export interface Finding {
  id: string;
  scan_id: string;
  tenant_id: string;
  rule_id: string;
  service_name: 'S3' | 'IAM' | 'EC2' | 'KMS' | 'CloudTrail' | string;
  resource_arn: string;
  severity: Severity;
  status: FindingStatus;
  title: string;
  description?: string;
  impact?: string;
  remediation_json: RemediationPayload;
  compliance_controls: string[];
  detected_at: string;
}

export interface CloudAccount {
  id: string;
  tenant_id: string;
  provider: 'AWS' | 'AZURE' | 'GCP';
  account_number: string;
  account_alias: string;
  role_arn: string;
  external_id: string;
  connection_status: 'ACTIVE' | 'PENDING' | 'ERROR' | 'DISCONNECTED';
  created_at: string;
}

export interface GRCControl {
  id: string;
  control_id: string;
  title: string;
  status: 'PASS' | 'FAIL' | 'NEEDS_REVIEW';
  mapped_rules: string[];
  description: string;
}

export interface GRCFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  score: number;
  active_accounts: number;
  passed_controls: number;
  total_controls: number;
  status: 'ACTIVE' | 'INACTIVE';
  controls: GRCControl[];
}

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: 'SUPER_ADMIN' | 'ACCOUNT_ADMIN' | 'ANALYST' | 'AUDITOR' | 'VIEWER';
  is_active: boolean;
}

export interface Tenant {
  id: string;
  company_name: string;
  subscription_plan: 'FREE' | 'PRO' | 'ENTERPRISE';
}

export interface ThreatScoreSummary {
  threat_score: number;
  risk_level: 'Critical' | 'High' | 'Medium' | 'Low Risk';
  total_findings: number;
  findings_delta?: string;
  scanned_resources: string;
  active_policies: number;
  severity_breakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}
