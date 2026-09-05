import os
import re
from typing import Any, Dict, List, Optional


SECRET_PATTERNS = [
    {
        "type": "AWS Access Key ID",
        "pattern": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "rule_id": "secrets.exposed-aws-access-key",
        "severity": "CRITICAL",
        "description": "Plaintext AWS Access Key ID detected in configuration or source file.",
        "impact": "Exposed credentials can lead to unauthorized access, resource compromise, and data breach."
    },
    {
        "type": "GitHub Personal Access Token",
        "pattern": re.compile(r"\b(ghp_[A-Za-z0-9_]{36})\b"),
        "rule_id": "secrets.exposed-github-token",
        "severity": "CRITICAL",
        "description": "Plaintext GitHub Personal Access Token detected.",
        "impact": "Exposed tokens allow malicious actors to compromise source repositories and automated pipelines."
    },
    {
        "type": "Private RSA/EC/SSH Key",
        "pattern": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "rule_id": "secrets.exposed-private-key",
        "severity": "CRITICAL",
        "description": "Unencrypted cryptographic private key detected.",
        "impact": "Enables impersonation, decryption of communications, and unauthorized infrastructure access."
    },
    {
        "type": "Slack API Token",
        "pattern": re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b"),
        "rule_id": "secrets.exposed-slack-token",
        "severity": "HIGH",
        "description": "Plaintext Slack API/Bot Token detected.",
        "impact": "Allows attackers to eavesdrop on private enterprise communication channels."
    }
]

IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build"
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".lock", ".pyc", ".db", ".sqlite"
}


def redact_secret(token: str) -> str:
    """Mask the secret, keeping only the first 4 characters for identification."""
    if len(token) <= 6:
        return "******"
    prefix = token[:4]
    masked = "*" * (len(token) - 4)
    return f"{prefix}{masked}"


def scan_content(text: str, filename: str = "memory_snippet") -> List[Dict[str, Any]]:
    """Scan string content for secrets and return sanitized finding records."""
    findings = []
    lines = text.splitlines()

    for pattern_def in SECRET_PATTERNS:
        regex = pattern_def["pattern"]
        for line_num, line in enumerate(lines, 1):
            match = regex.search(line)
            if match:
                matched_raw = match.group(0)
                masked = redact_secret(matched_raw)
                findings.append({
                    "rule_id": pattern_def["rule_id"],
                    "service_name": "Secrets",
                    "resource_arn": f"arn:cloudguard:local-workspace:{filename}#L{line_num}",
                    "severity": pattern_def["severity"],
                    "title": f"Exposed {pattern_def['type']} in {os.path.basename(filename)}",
                    "description": pattern_def["description"],
                    "impact": pattern_def["impact"],
                    "controls": ["CIS AWS 1.14", "ISO 27001 A.8.12", "DPDPA Section 8(5)"],
                    "evidence": {
                        "file": filename,
                        "line": line_num,
                        "secret_type": pattern_def["type"],
                        "masked_match": masked,
                        "redacted": True
                    },
                    "remediation": {
                        "explanation": f"Revoke the exposed {pattern_def['type']} immediately, audit access logs for unauthorized use, and store secrets in AWS Secrets Manager or HashiCorp Vault.",
                        "cli": "aws secretsmanager create-secret --name /prod/credentials ...",
                        "terraform": "# Use aws_secretsmanager_secret rather than hardcoded environment variables."
                    }
                })
    return findings


def scan_local_path(target_path: str, max_files: int = 150) -> List[Dict[str, Any]]:
    """Walk a directory path and scan text files for secrets without leaking credentials."""
    all_findings = []
    files_scanned = 0

    if os.path.isfile(target_path):
        try:
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                return scan_content(f.read(), filename=target_path)
        except Exception:
            return []

    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORE_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    all_findings.extend(scan_content(content, filename=file_path))
                files_scanned += 1
                if files_scanned >= max_files:
                    return all_findings
            except Exception:
                continue

    return all_findings

