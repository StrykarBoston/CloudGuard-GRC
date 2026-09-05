7/29/26, 12:19 AM                                             UI/UX Design Brief - CloudGuard GRC




          UI/UX Design Brief & Stitch MCP Specification


              App Name: CloudGuard GRC (AntiGravity Platform Architecture)[cite: 1]

              Document Version: 1.0.0 (UI/UX System, Component Design Tokens & Stitch Prompts)

              Target Aesthetic: High-Density Enterprise Cybersecurity Dashboard (Dark/Light Seamless Support)
              [cite: 1]

              Integration Standard: Tailored for Generative UI rendering via Stitch MCP Server




          1. Design Style & Overall Aesthetic

              Aesthetic Persona: Modern Enterprise Cybersecurity Posture Management (CSPM) & GRC
              Automation[cite: 1]. Sleek, professional, precise, and authoritative—resembling high-end platforms like
              Wiz.io, Datadog, and Linear.app.
              Visual Tone: High data-density with minimal noise. Interfaces must prioritize fast triage, clear risk
              urgency, and zero visual clutter[cite: 1].
              Theme Modes:
                 Dark Mode (Default/Recommended): Deep slate/navy background ( #090d16 ) with high-contrast
                    glowing accents for risk scores and alert badges.
                    Light Mode: Cool gray canvas ( #f8fafc ) with dark slate text ( #0f172a ) and subtle card borders.
              Stitch MCP System Rule: All UI components generated via the Stitch MCP server must strictly utilize
              TailwindCSS utility classes and standard shadcn/ui primitives.


          2. Color Palette & Design Tokens

           Category               Token Name          Hex Code        Usage & UI Context

           Background              bg-dark-
                                                                      Main application canvas in Dark Mode.
           (Dark)                 canvas               #090d16

                                   bg-dark-
           Surface / Card                                             Dashboard cards, modals, and detail drawers.
                                  surface              #131c2e

                                                                      Primary action buttons, active navigation states,
           Brand Primary           brand-primary
                                                       #2563eb        interactive links.

                                   severity-                          Exposed keys, public S3 buckets, root MFA disabled
           Critical Severity
                                  critical             #ef4444        badges/alerts[cite: 1].

                                                                      Overly permissive IAM roles, unencrypted
           High Severity           severity-high
                                                       #f97316        databases[cite: 1].

                                   severity-                          Stale IAM keys (>90 days), missing log retention
           Medium Severity
                                  medium               #eab308        policies[cite: 1].



file:///D:/Downloads/gemini-code-1785264552560.html                                                                        1/4
7/29/26, 12:19 AM                                            UI/UX Design Brief - CloudGuard GRC

           Category               Token Name          Hex Code       Usage & UI Context

                                                                     Informational configuration drift or minor best-practice
           Low Severity            severity-low
                                                      #3b82f6        flags[cite: 1].

           Passed /                                                  100% compliance checks passed, secure status
                                   status-passed
           Compliant                                  #22c55e        badges[cite: 1].



          3. Typography & Font System

              Primary UI Font: Inter , -apple-system , sans-serif (Clean, highly legible at small font sizes).
              Code & IaC Snippets Font: JetBrains Mono , Fira Code , monospace (Used for AWS ARNs,
              Terraform code fixes, CLI commands)[cite: 1].
              Type Scale Hierarchy:
                 Display / Score : 36px / Bold (e.g., ThreatScore Gauge "84/100")[cite: 1]
                    Header 1 (Page Titles) : 24px / SemiBold
                    Header 2 (Card Titles) : 18px / Medium
                    Body Regular : 14px / Regular (Table rows, description text)
                    Caption / Badges : 12px / Medium (Pills, timestamp labels, severity chips)


          4. Component Styling & Patterns

          Cards & Containers

              Border Style: Thin 1px border using border-slate-800 (Dark) or border-slate-200 (Light).
              Corner Radius: rounded-lg (8px radius) for widgets; rounded-xl (12px radius) for modals.
              Elevation / Shadow: Subtle ambient drop-shadow ( shadow-sm ). Avoid heavy, distracting shadows.

          Buttons & Interactive Elements

              Primary CTA (Scan / Fix): Solid Cyber Blue ( bg-blue-600 hover:bg-blue-500 text-white ) with focus
              ring[cite: 1].
              Remediate / Auto-Fix CTA: Destructive/Accent subtle glow ( bg-red-500/10 text-red-400 border
              border-red-500/30 hover:bg-red-500/20 )[cite: 1].
              Secondary / Outline: Transparent background with border ( border-slate-700 hover:bg-slate-800
              text-slate-200 ).


          Data Tables & Severity Badges

              Table Layout: Compact padding ( py-3 px-4 ), sticky table headers, zebra hover effect ( hover:bg-
              slate-800/50 ).
              Inline Severity Pills: Rounded full pills ( rounded-full px-2.5 py-0.5 text-xs font-semibold ) with
              10% background opacity matching border and text colors (e.g., Critical: bg-red-500/10 text-red-400
              border border-red-500/20 )[cite: 1].


          5. Dashboard Layout Architecture

          The main dashboard ( SCR-03 ) uses a structured 12-column responsive grid layout[cite: 1]:

              Top Banner (Row 1 - Full Width): Account Context Header, Quick Scan Trigger button, and Overall
              ThreatScore Radial Gauge (0-100 score)[cite: 1].


file:///D:/Downloads/gemini-code-1785264552560.html                                                                             2/4
7/29/26, 12:19 AM                                           UI/UX Design Brief - CloudGuard GRC

              Key Metrics (Row 2 - 4 Columns): 4 stat-cards showing Critical Risks Count, Active AWS Accounts, CIS
              Compliance %, and DPDPA Compliance %[cite: 1].
              Risk & Compliance Analytics (Row 3 - 8 cols / 4 cols split):
                    Left 8 Cols: Compliance Framework Progress Bars (CIS AWS, DPDPA, GDPR, ISO 27001)[cite: 1].
                    Right 4 Cols: Risk Severity Distribution Donut Chart (Critical, High, Med, Low)[cite: 1].
              Urgent Action Items (Row 4 - Full Width): Top 5 Critical Misconfigurations Table with instant "View Fix"
              drawer triggers[cite: 1].


          6. Mobile & Desktop Responsive Behavior

              Desktop (≥ 1024px): Fixed 256px collapsible left sidebar, multi-column dashboard widgets, side-drawer
              overlays for finding details[cite: 1].
              Tablet (768px - 1023px): Sidebar collapses to 64px icon-only rail; 2-column grid reflow for stat widgets.
              Mobile (< 768px): Sidebar turns into a slide-over mobile sheet menu; data tables convert to swipeable
              card lists with sticky filter bar at top.


          7. User Experience Principles (UX Directives)

           1. Alert Noise Reduction: Group duplicate findings by cloud service/region to prevent "Alert Fatigue"[cite:
              1]. Highlight the top 5 issues that eliminate 80% of total risk first[cite: 1].
           2. Actionable Over Descriptive: Every finding card MUST display immediate solution code (Terraform /
              AWS CLI) alongside the risk explanation[cite: 1].
           3. Frictionless Role Views: Automatically adapt UI density based on user role (e.g., show code/CLI tools to
              DevOps engineers; show compliance charts and PDF export options to Auditors)[cite: 1].


          8. Stitch MCP Server Prompt Specifications

          Use these exact prompt templates when invoking the Stitch MCP Server to generate application
          components:

          Stitch Prompt 1: Global Security Dashboard Shell



            stitch_generate_component --name "GlobalSecurityDashboard" --prompt "Create a dark-mode enterprise
            cloud security dashboard for CloudGuard GRC using TailwindCSS and React. Include a top bar with an
            account switcher and 'Run On-Demand Scan' button. Top section features a ThreatScore radial gauge
            (84/100) and 4 metric cards (Critical Risks: 2, AWS Accounts: 3, CIS Score: 82%, DPDPA Score: 90%).
            Middle section includes a compliance framework progress list (CIS AWS, DPDPA, GDPR) and a severity
            donut chart. Bottom section shows a findings table with severity pills (Red for Critical, Orange
            for High) and a 'View Fix' button on each row. Background should be #090d16 and card surfaces
            #131c2e with border #1e293b."




          Stitch Prompt 2: Finding Detail & Remediation Drawer



            stitch_generate_component --name "FindingDetailDrawer" --prompt "Build a slide-over drawer
            component for a cloud security finding: 'Unencrypted S3 Bucket: data-archive'. Include a Critical
            Red badge, mapped compliance frameworks (CIS AWS 2.1.1, DPDPA Sec 8), resource ARN string, and a
            tabbed remediation section ('AWS CLI', 'Terraform Code'). The Terraform tab must render a syntax-
            highlighted code block with a 'Copy Code' button. Include a primary action button 'Auto-Remediate
            (Lambda)' and a secondary button 'Mark as Suppressed'."



file:///D:/Downloads/gemini-code-1785264552560.html                                                                       3/4
7/29/26, 12:19 AM                                        UI/UX Design Brief - CloudGuard GRC

          Stitch Prompt 3: Compliance Framework Matrix View



            stitch_generate_component --name "ComplianceMatrixView" --prompt "Design a GRC compliance report
            page for DPDPA and CIS AWS benchmarks. Include a top header with 'Overall Compliance Score: 85%'
            and an 'Export Audit PDF' button. Render a data grid where rows represent security controls (e.g.,
            '1.1 Root Account MFA Enabled', '2.1 S3 Bucket Encryption') and columns show Pass/Fail badges per
            AWS account. Use green pills for Pass and red pills for Fail with hover tooltips."




file:///D:/Downloads/gemini-code-1785264552560.html                                                              4/4
