7/29/26, 12:26 AM                                          Backend Schema Document - CloudGuard GRC




          Backend Database Schema & Data Ownership
          Specification


              App Name: CloudGuard GRC (AntiGravity Platform Architecture)[cite: 1]

              Database Engine: AWS RDS PostgreSQL v15+ (Relational Core) + AWS S3 (Raw Audits)[cite: 1]

              Document Version: 1.0.0 (Data Models, Relationships, Indexes & Multi-Tenancy)




          1. Entity Relationship Overview & Foreign Key Hierarchy

          CloudGuard GRC utilizes a strict multi-tenant database design where all core application tables cascade
          down from a master tenants organization record[cite: 1]. Data isolation is guaranteed at the API and
          database levels via Tenant IDs and PostgreSQL Row-Level Security (RLS) policies[cite: 1].


            ┌─────────────────┐             1:N       ┌─────────────────┐       1:N        ┌─────────────────┐
            │     tenants     │ ───────────────►│      users      │ ───────────────►│    sessions     │
            └─────────────────┘                 └─────────────────┘                 └─────────────────┘
                       │
                       │ 1:N
                     ▼
            ┌─────────────────┐             1:N       ┌─────────────────┐       1:N        ┌─────────────────┐
            │ cloud_accounts │ ───────────────►│      scans      │ ───────────────►│    findings     │
            └─────────────────┘                └─────────────────┘                 └─────────────────┘
                       │                                                                              │
                       │ 1:N                                                                          │ M:N
                     ▼                                                                              ▼
            ┌─────────────────┐                                                            ┌─────────────────┐
            │   audit_logs    │                                                            │    compliance_      │
            └─────────────────┘                                                            │   rule_mappings     │
                                                                                           └─────────────────┘




          2. Table Definitions & Column Specifications

          Table 1: tenants (Organizations / Enterprise Accounts)

          Stores customer tenant metadata, plan tiers, and organization settings[cite: 1].


           Column Name               Data Type         Constraints                         Description

                                                       PRIMARY KEY, DEFAULT                Unique global tenant
            id                       UUID
                                                       gen_random_uuid()                   identification string.

                                                                                           Name of the customer
            company_name             VARCHAR(255)      NOT NULL
                                                                                           enterprise or startup[cite: 1].



file:///D:/Downloads/gemini-code-1785264943159.html                                                                          1/6
7/29/26, 12:26 AM                                            Backend Schema Document - CloudGuard GRC

           Column Name               Data Type            Constraints                           Description

                                                                                                Plan tier ('FREE', 'PRO',
            subscription_plan        VARCHAR(50)          NOT NULL, DEFAULT 'FREE'
                                                                                                'ENTERPRISE')[cite: 1].

                                                          NOT NULL, DEFAULT
            created_at               TIMESTAMPTZ                                                Tenant registration timestamp.
                                                          CURRENT_TIMESTAMP

                                                          NOT NULL, DEFAULT                     Last organization update
            updated_at               TIMESTAMPTZ
                                                          CURRENT_TIMESTAMP                     timestamp.


          Table 2: users (User Accounts & IAM Roles)

          Stores registered user identities, password hashes, and assigned application roles[cite: 1].


           Column Name          Data Type             Constraints                     Description

                                                      PRIMARY KEY, DEFAULT
            id                  UUID                                                  Unique user identifier.
                                                      gen_random_uuid()

                                                      FOREIGN KEY -> tenants(id)
            tenant_id           UUID                                                  Associated parent organization ID.
                                                      ON DELETE CASCADE

                                                                                      User email address (used for login)
            email               VARCHAR(255)          NOT NULL, UNIQUE
                                                                                      [cite: 1].

                                                                                      Argon2id or Bcrypt secure password
            password_hash       VARCHAR(255)          NOT NULL
                                                                                      digest.

            full_name           VARCHAR(100)          NOT NULL                        User display name[cite: 1].

                                                                                      Role ('SUPER_ADMIN',
            role                VARCHAR(50)           NOT NULL, DEFAULT 'VIEWER'      'ACCOUNT_ADMIN', 'ANALYST',
                                                                                      'AUDITOR', 'VIEWER')[cite: 1].

            is_active           BOOLEAN               NOT NULL, DEFAULT TRUE          Account status toggle.

                                                      NOT NULL, DEFAULT
            created_at          TIMESTAMPTZ                                           Record creation timestamp.
                                                      CURRENT_TIMESTAMP


          Table 3: sessions (Auth & Session Handling)

          Tracks active JWT refresh token hashes and device session states[cite: 1].


           Column Name                 Data Type           Constraints                             Description

                                                           PRIMARY KEY, DEFAULT
            id                         UUID                                                        Session identifier token.
                                                           gen_random_uuid()

                                                           FOREIGN KEY -> users(id) ON
            user_id                    UUID                                                        Associated user record.
                                                           DELETE CASCADE

                                                                                                   Hashed refresh token for
            refresh_token_hash         VARCHAR(255)        NOT NULL, UNIQUE
                                                                                                   OAuth2 token rotation.




file:///D:/Downloads/gemini-code-1785264943159.html                                                                              2/6
7/29/26, 12:26 AM                                         Backend Schema Document - CloudGuard GRC

           Column Name                 Data Type       Constraints                           Description

                                                                                             IPv4/IPv6 address of the
            ip_address                 VARCHAR(45)     NULLABLE
                                                                                             login request.

                                                                                             Browser/CLI client user
            user_agent                 TEXT            NULLABLE
                                                                                             agent string.

                                                                                             Expiration timestamp for the
            expires_at                 TIMESTAMPTZ     NOT NULL
                                                                                             refresh session.

                                                       NOT NULL, DEFAULT                     Session issuance
            created_at                 TIMESTAMPTZ
                                                       CURRENT_TIMESTAMP                     timestamp.


          Table 4: cloud_accounts (Connected Cloud Accounts)

          Stores onboarded AWS, Azure, and GCP environment connection credentials[cite: 1].


           Column Name               Data Type         Constraints                      Description

                                                       PRIMARY KEY, DEFAULT
            id                       UUID                                               Internal account UUID.
                                                       gen_random_uuid()

                                                       FOREIGN KEY -> tenants(id) ON
            tenant_id                UUID                                               Parent tenant ownership link.
                                                       DELETE CASCADE

                                                                                        Cloud provider ('AWS', 'AZURE',
            provider                 VARCHAR(20)       NOT NULL
                                                                                        'GCP')[cite: 1].

                                                                                        AWS 12-digit Account ID or Azure
            account_number           VARCHAR(100)      NOT NULL
                                                                                        Subscription ID[cite: 1].

                                                                                        User-defined display name (e.g.,
            account_alias            VARCHAR(100)      NOT NULL
                                                                                        'Production-AWS')[cite: 1].

                                                                                        AWS Read-Only IAM Role ARN
            role_arn                 VARCHAR(255)      NOT NULL
                                                                                        (`arn:aws:iam::...`)[cite: 1].

                                                                                        Unique string preventing
            external_id              VARCHAR(255)      NOT NULL
                                                                                        Confused Deputy attacks[cite: 1].

                                                                                        Status ('ACTIVE', 'PENDING',
                                                       NOT NULL, DEFAULT
            connection_status        VARCHAR(50)                                        'ERROR', 'DISCONNECTED')
                                                       'PENDING'
                                                                                        [cite: 1].

                                                       NOT NULL, DEFAULT
            created_at               TIMESTAMPTZ                                        Onboarding timestamp[cite: 1].
                                                       CURRENT_TIMESTAMP


          Table 5: scans (Scan Execution Jobs)

          Records scan job history, execution states, and aggregated risk summaries[cite: 1].


           Column Name              Data Type         Constraints                        Description

                                                      PRIMARY KEY, DEFAULT
            id                      UUID                                                 Scan execution ID.
                                                      gen_random_uuid()


file:///D:/Downloads/gemini-code-1785264943159.html                                                                         3/6
7/29/26, 12:26 AM                                         Backend Schema Document - CloudGuard GRC

           Column Name              Data Type         Constraints                         Description

                                                      FOREIGN KEY ->
                                                                                          Target cloud account being
            cloud_account_id        UUID              cloud_accounts(id) ON DELETE
                                                                                          audited[cite: 1].
                                                      CASCADE

                                                                                          Trigger origin ('MANUAL',
            trigger_type            VARCHAR(50)       NOT NULL                            'SCHEDULED', 'CI_CD_HOOK')
                                                                                          [cite: 1].

                                                                                          Job state ('QUEUED',
                                                                                          'IN_PROGRESS',
            status                  VARCHAR(50)       NOT NULL, DEFAULT 'QUEUED'
                                                                                          'COMPLETED', 'FAILED')[cite:
                                                                                          1].

                                                                                          Calculated weighted risk score (0
            threat_score            INTEGER           NULLABLE
                                                                                          - 100)[cite: 1].

                                                                                          Total count of misconfigurations
            total_findings          INTEGER           DEFAULT 0
                                                                                          detected[cite: 1].

                                                                                          S3 object key containing raw
            raw_log_s3_key          VARCHAR(255)      NULLABLE
                                                                                          JSON scan payload[cite: 1].

                                                      NOT NULL, DEFAULT
            started_at              TIMESTAMPTZ                                           Scan execution start time.
                                                      CURRENT_TIMESTAMP

                                                                                          Scan job completion
            completed_at            TIMESTAMPTZ       NULLABLE
                                                                                          timestamp[cite: 1].


          Table 6: findings (Security Misconfigurations & Exposed Secrets)

          Stores detailed policy violations, risk severities, and remediation code snippets[cite: 1].


           Column Name              Data Type         Constraints                         Description

                                                      PRIMARY KEY, DEFAULT
            id                      UUID                                                  Finding UUID.
                                                      gen_random_uuid()

                                                      FOREIGN KEY -> scans(id) ON
            scan_id                 UUID                                                  Origin scan job link[cite: 1].
                                                      DELETE CASCADE

                                                      FOREIGN KEY -> tenants(id) ON       Tenant isolation boundary
            tenant_id               UUID
                                                      DELETE CASCADE                      key[cite: 1].

                                                                                          Benchmark rule key (e.g., 'cis-
            rule_id                 VARCHAR(100)      NOT NULL
                                                                                          aws-2.1.1-s3-public')[cite: 1].

                                                                                          AWS service ('S3', 'IAM', 'EC2',
            service_name            VARCHAR(50)       NOT NULL
                                                                                          'RDS', 'KMS')[cite: 1].

                                                                                          Target AWS resource string[cite:
            resource_arn            TEXT              NOT NULL
                                                                                          1].

                                                                                          Severity ('CRITICAL', 'HIGH',
            severity                VARCHAR(20)       NOT NULL                            'MEDIUM', 'LOW', 'INFO')[cite:
                                                                                          1].

file:///D:/Downloads/gemini-code-1785264943159.html                                                                           4/6
7/29/26, 12:26 AM                                            Backend Schema Document - CloudGuard GRC

           Column Name              Data Type            Constraints                        Description

                                                                                            Status ('OPEN', 'RESOLVED',
            status                  VARCHAR(50)          NOT NULL, DEFAULT 'OPEN'
                                                                                            'SUPPRESSED')[cite: 1].

                                                                                            Summary of the security
            title                   VARCHAR(255)         NOT NULL
                                                                                            vulnerability[cite: 1].

                                                                                            JSON object containing
            remediation_json        JSONB                NOT NULL                           Terraform and CLI fix
                                                                                            snippets[cite: 1].

                                                         NOT NULL, DEFAULT
            detected_at             TIMESTAMPTZ                                             First detection timestamp[cite: 1].
                                                         CURRENT_TIMESTAMP


          Table 7: audit_logs (System & Compliance Action Audit Trail)

          Stores chronological application action logs for compliance auditing and forensic tracking[cite: 1].


           Column Name          Data Type             Constraints                     Description

                                                      PRIMARY KEY, DEFAULT
            id                  UUID                                                  Audit entry UUID.
                                                      gen_random_uuid()

                                                      FOREIGN KEY -> tenants(id)
            tenant_id           UUID                                                  Associated organization ID[cite: 1].
                                                      ON DELETE CASCADE

                                                      FOREIGN KEY -> users(id) ON     User executing the action (NULL if
            user_id             UUID
                                                      DELETE SET NULL                 automated system)[cite: 1].

                                                                                      Action key (e.g., 'ACCOUNT_ADDED',
            action_type         VARCHAR(100)          NOT NULL
                                                                                      'FINDING_SUPPRESSED')[cite: 1].

                                                                                      Contextual details (IP address, affected
            metadata_json       JSONB                 NULLABLE
                                                                                      resource, parameters)[cite: 1].

                                                      NOT NULL, DEFAULT               Log timestamp (retained for 1+ years)
            created_at          TIMESTAMPTZ
                                                      CURRENT_TIMESTAMP               [cite: 1].


          Table 8: rules (Security Rules)

          Stores definitions of security rules that the scan engine executes.


           Column Name          Data Type             Constraints                     Description

                                                      PRIMARY KEY, DEFAULT
            id                  UUID                                                  Unique rule identifier.
                                                      gen_random_uuid()

                                                                                      Rule identifier (e.g., 'cis-aws-2.1.1').
            rule_id             VARCHAR(100)          NOT NULL, UNIQUE

                                                                                      Service (e.g., 'S3', 'IAM').
            service             VARCHAR(50)           NOT NULL

                                                                                      Severity (e.g., 'CRITICAL').
            severity            VARCHAR(20)           NOT NULL

                                                                                      Short description of the rule.
            title               VARCHAR(255)          NOT NULL

                                                      NOT NULL, DEFAULT
            created_at          TIMESTAMPTZ                                           Record creation timestamp.
                                                      CURRENT_TIMESTAMP


          Table 9: grc_frameworks (Compliance Frameworks)

          Stores supported compliance frameworks (e.g., CIS AWS, DPDPA, GDPR).


           Column Name          Data Type             Constraints                     Description

                                                      PRIMARY KEY, DEFAULT
            id                  UUID                                                  Unique framework identifier.
                                                      gen_random_uuid()

                                                                                      Framework name.
            name                VARCHAR(100)          NOT NULL, UNIQUE

                                                                                      Framework version or description.
            version             VARCHAR(50)           NULLABLE

                                                      NOT NULL, DEFAULT
            created_at          TIMESTAMPTZ                                           Record creation timestamp.
                                                      CURRENT_TIMESTAMP


          Table 10: grc_controls (Framework Controls)

          Stores individual controls within a GRC framework.


           Column Name          Data Type             Constraints                     Description

                                                      PRIMARY KEY, DEFAULT
            id                  UUID                                                  Unique control identifier.
                                                      gen_random_uuid()

                                                      FOREIGN KEY ->
            framework_id        UUID                  grc_frameworks(id) ON DELETE    Associated framework ID.
                                                      CASCADE

                                                                                      Control identifier (e.g., '1.1').
            control_id          VARCHAR(100)          NOT NULL

                                                                                      Description of the control.
            title               VARCHAR(255)          NOT NULL

                                                      NOT NULL, DEFAULT
            created_at          TIMESTAMPTZ                                           Record creation timestamp.
                                                      CURRENT_TIMESTAMP


          Table 11: finding_control_mappings (Findings to Controls)

          Maps security findings to GRC controls.


           Column Name          Data Type             Constraints                     Description

                                                      PRIMARY KEY, DEFAULT
            id                  UUID                                                  Unique mapping identifier.
                                                      gen_random_uuid()

                                                      FOREIGN KEY -> findings(id)
            finding_id          UUID                                                  Associated finding ID.
                                                      ON DELETE CASCADE

                                                      FOREIGN KEY ->
            control_id          UUID                  grc_controls(id) ON DELETE      Associated control ID.
                                                      CASCADE

                                                      NOT NULL, DEFAULT
            created_at          TIMESTAMPTZ                                           Record creation timestamp.
                                                      CURRENT_TIMESTAMP


          3. Indexes & Database Performance Tuning

          To ensure fast REST API response times (< 200ms p95) and prevent query lag during large multi-account
          scans, the following index structures are enforced[cite: 1]:


            -- Fast filtering of findings by Tenant, Severity, and Status
            CREATE INDEX idx_findings_tenant_severity
            ON findings (tenant_id, severity, status);

            -- Rapid lookup for findings under a specific cloud account scan
            CREATE INDEX idx_findings_scan_id
            ON findings (scan_id);


            -- JSONB GIN Index for fast querying of Terraform remediation snippets inside JSON
            CREATE INDEX idx_findings_remediation_gin
            ON findings USING GIN (remediation_json);



file:///D:/Downloads/gemini-code-1785264943159.html                                                                               5/6
7/29/26, 12:26 AM                                             Backend Schema Document - CloudGuard GRC
            -- Fast user lookup during authentication
            CREATE INDEX idx_users_email
            ON users (email);

            -- Query optimization for historical audit log exports
            CREATE INDEX idx_audit_logs_tenant_created
            ON audit_logs (tenant_id, created_at DESC);




          4. Application RBAC & Row-Level Security (RLS) Rules

          Role Permission Matrix

                                  Onboard             Trigger                            Remediate /     Export Audit
           Application Role                                          View Findings
                                  Accounts            Scans                              Suppress        Reports

           Super Admin            ✓[cite: 1]          ✓[cite: 1]     ✓[cite: 1]          ✓[cite: 1]      ✓[cite: 1]

           Cloud Account
                                  ✓[cite: 1]          ✓[cite: 1]     ✓[cite: 1]          ✓[cite: 1]      ✓[cite: 1]
           Admin

           Security Analyst       ✗[cite: 1]          ✓[cite: 1]     ✓[cite: 1]          ✓[cite: 1]      ✓[cite: 1]

           Auditor (Read-
                                  ✗[cite: 1]          ✗[cite: 1]     ✓[cite: 1]          ✗[cite: 1]      ✓[cite: 1]
           Only)

                                                                     ✓ (Summary Only)
           Viewer                 ✗[cite: 1]          ✗[cite: 1]                         ✗[cite: 1]      ✗[cite: 1]
                                                                     [cite: 1]


          Data Ownership & Multi-Tenant Isolation Enforcement

              Database Row-Level Security (RLS): PostgreSQL Row-Level Security is enabled on the findings ,
               cloud_accounts , and audit_logs tables[cite: 1].
              Session Context Injection: Upon processing an authenticated REST API request, the FastAPI backend
              injects the decoded JWT's tenant_id into the active database transaction context using SET LOCAL
              app.current_tenant_id = 'tenant_uuid_here'; .
              RLS Isolation Policy Example:


                -- Enable RLS on Findings Table
                ALTER TABLE findings ENABLE ROW LEVEL SECURITY;

                -- Enforce strict isolation: Users can only query findings matching their tenant context
                CREATE POLICY tenant_isolation_policy ON findings
                FOR ALL
                USING (tenant_id = current_setting('app.current_tenant_id')::UUID);




file:///D:/Downloads/gemini-code-1785264943159.html                                                                     6/6
