#!/usr/bin/env python3
"""
Secret Scanner — Security Pre-commit Hook
==========================================
Scans the codebase for accidentally committed API keys, passwords,
and sensitive credentials.

This script is designed to be used as a pre-commit hook (see
.pre-commit-config.yaml) to prevent secrets from ever entering
the git history.

Course Concept: Security Features
Demonstrates "shift-left" security by catching secrets before
they are committed, rather than after a breach occurs.

Usage:
    python security/scan_secrets.py [directory]

Exit codes:
    0 — No secrets found
    1 — Secrets detected (blocks commit)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ── Secret Patterns ──────────────────────────────────────────────────────────
# Each pattern is a (regex, description) tuple.
# These detect common API key formats without false positives on template files.

SECRET_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # OpenAI-compatible API keys (e.g., DeepSeek, OpenAI)
    (re.compile(r'sk-[a-zA-Z0-9]{48,}'), "OpenAI-compatible API Key"),
    # Anthropic API keys
    (re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}'), "Anthropic API Key"),
    # OpenAI API keys
    (re.compile(r'sk-proj-[a-zA-Z0-9]{20,}'), "OpenAI Project Key"),
    # GitHub tokens
    (re.compile(r'gh[pousr]_[a-zA-Z0-9]{20,}'), "GitHub Personal Access Token"),
    # Google API keys
    (re.compile(r'AIza[0-9A-Za-z\-_]{35}'), "Google API Key"),
    # Generic API key patterns
    (re.compile(r'api[_-]?key\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']', re.IGNORECASE),
     "Generic API Key assignment"),
    # AWS keys
    (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS Access Key ID"),
    (re.compile(r'aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\'][A-Za-z0-9/+=]{20,}["\']', re.IGNORECASE),
     "AWS Secret Access Key"),
    # Private keys
    (re.compile(r'-----BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY-----'),
     "Private Key (RSA/EC/SSH)"),
    # Generic password patterns
    (re.compile(r'password\s*[:=]\s*["\'][^"\']+["\']', re.IGNORECASE),
     "Hardcoded password"),
    # JWT tokens
    (re.compile(r'eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{10,}'),
     "JWT Token"),
]

# ── Files to Skip ────────────────────────────────────────────────────────────

SKIP_PATTERNS = [
    ".env",                    # Gitignored — user's local keys
    ".env.template",           # Template files are safe
    "scan_secrets.py",         # This file itself
    "prompts.md",              # Original hackathon file (non-code)
    "requirements_desc.md",    # Original hackathon file (non-code)
    "idea_formulation.md",     # Original hackathon file (non-code)
    "*.pyc",
    "__pycache__",
    ".git/",
    "node_modules/",
    "*.ipynb_checkpoints",
    "memory.json",            # Memory store may contain demo data
    "*.svg",
    "*.png",
    "*.jpg",
    "*.gif",
]

# ── Maximum line length check (catches accidental key paste) ─────────────────

MAX_LINE_LENGTH = 500  # Lines longer than this are suspicious


def should_skip(file_path: str) -> bool:
    """Check if a file should be skipped based on patterns."""
    file_name = os.path.basename(file_path)
    for pattern in SKIP_PATTERNS:
        if pattern.startswith("*"):
            if file_name.endswith(pattern[1:]):
                return True
        elif pattern.endswith("/"):
            if pattern in file_path:
                return True
        elif file_name == pattern:
            return True
    return False


def scan_file(file_path: str) -> List[Tuple[int, str, str]]:
    """
    Scan a single file for secrets.

    Args:
        file_path: Path to the file to scan.

    Returns:
        List of (line_number, secret_type, line_content) tuples for matches.
    """
    findings = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError):
        return findings

    for line_num, line in enumerate(lines, 1):
        # Check line length
        if len(line) > MAX_LINE_LENGTH:
            findings.append((
                line_num,
                "Suspiciously long line",
                f"Line is {len(line)} characters (max {MAX_LINE_LENGTH})",
            ))
            continue

        # Check against secret patterns
        for pattern, description in SECRET_PATTERNS:
            if pattern.search(line):
                # Show sanitized match
                sanitized = pattern.sub("***REDACTED***", line).strip()
                findings.append((line_num, description, sanitized))

    return findings


def scan_directory(directory: str = ".") -> dict[str, list]:
    """
    Scan all files in a directory recursively for secrets.

    Args:
        directory: Root directory to scan.

    Returns:
        Dict mapping file paths to their findings lists.
    """
    results = {}
    total_files_scanned = 0

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories and virtual environments
        dirs[:] = [d for d in dirs if not d.startswith(".") or d == ".git"]

        for file_name in files:
            file_path = os.path.join(root, file_name)

            if should_skip(file_path):
                continue

            findings = scan_file(file_path)
            if findings:
                results[file_path] = findings
            total_files_scanned += 1

    return results


def safe_print(text: str) -> None:
    """Print text safely across platforms, handling Unicode errors on Windows."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: strip emoji and special chars for Windows GBK terminals
        import unicodedata
        clean = ""
        for ch in text:
            if unicodedata.category(ch) != "So":  # Skip emoji/symbols
                clean += ch
            else:
                clean += "[?]"
        print(clean)


def main() -> int:
    """Main entry point. Returns exit code."""
    target = sys.argv[1] if len(sys.argv) > 1 else "."

    safe_print("=" * 60)
    safe_print("[SECURITY] Secret Scanner -- Personal Knowledge Concierge")
    safe_print("=" * 60)
    safe_print(f"Scanning: {os.path.abspath(target)}")
    safe_print("")

    results = scan_directory(target)

    total_findings = sum(len(v) for v in results.values())

    if total_findings == 0:
        safe_print("[OK] No secrets detected! Code is clean.")
        safe_print(f"     Scanned files (with findings: 0)")
        return 0

    # Report findings
    safe_print(f"[WARNING] {total_findings} potential secret(s) found!")
    safe_print("")
    for file_path, findings in results.items():
        safe_print(f"  FILE: {file_path}:")
        for line_num, secret_type, context in findings:
            safe_print(f"   Line {line_num}: [{secret_type}]")
            safe_print(f"   -> {context[:120]}")
        safe_print("")

    safe_print("[BLOCKED] Commit blocked! Remove secrets before committing.")
    safe_print("   - Use environment variables (see .env.template)")
    safe_print("   - Add sensitive files to .gitignore")
    safe_print("   - If this is a false positive, update SKIP_PATTERNS")
    return 1


if __name__ == "__main__":
    sys.exit(main())
