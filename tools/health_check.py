#!/usr/bin/env python3
"""
Eidolon health check — automated survival verification.

Run at the start of each heartbeat to catch problems early.
Returns a structured report. Exit code 0 = healthy, 1 = issues found.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent.resolve()

CRITICAL_FILES = [
    "soul.md",
    "memory/scratchpad.md",
    "main.py",
    "CONSTITUTION.md",
    ".claude/CLAUDE.md",
]


def check_files() -> list[dict]:
    """Verify critical files exist and aren't empty."""
    issues = []
    for rel_path in CRITICAL_FILES:
        full_path = REPO_DIR / rel_path
        if not full_path.exists():
            issues.append({"severity": "critical", "msg": f"MISSING: {rel_path}"})
        elif full_path.stat().st_size == 0:
            issues.append({"severity": "critical", "msg": f"EMPTY: {rel_path}"})
    return issues


def check_disk() -> list[dict]:
    """Check disk space. Warn if less than 1GB free."""
    issues = []
    usage = shutil.disk_usage(REPO_DIR)
    free_gb = usage.free / (1024 ** 3)
    if free_gb < 0.5:
        issues.append({"severity": "critical", "msg": f"Disk critically low: {free_gb:.1f}GB free"})
    elif free_gb < 1.0:
        issues.append({"severity": "warning", "msg": f"Disk low: {free_gb:.1f}GB free"})
    return issues


def check_cron() -> list[dict]:
    """Verify heartbeat cron job exists."""
    issues = []
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, timeout=5,
        )
        if "main.py" not in result.stdout:
            issues.append({"severity": "critical", "msg": "Cron job for main.py not found"})
    except Exception as e:
        issues.append({"severity": "warning", "msg": f"Could not check cron: {e}"})
    return issues


def check_git() -> list[dict]:
    """Check git status and last commit."""
    issues = []
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H %s", "--"],
            capture_output=True, text=True, timeout=5,
            cwd=REPO_DIR,
        )
        if result.returncode != 0:
            issues.append({"severity": "critical", "msg": "Git log failed"})
    except Exception as e:
        issues.append({"severity": "critical", "msg": f"Git error: {e}"})
    return issues


def check_identity() -> list[dict]:
    """Verify soul.md still reads like a manifesto, not a task list."""
    issues = []
    soul_path = REPO_DIR / "soul.md"
    if soul_path.exists():
        content = soul_path.read_text()
        # Simple heuristics for identity decay
        task_markers = content.count("- [ ]") + content.count("- [x]") + content.count("TODO")
        if task_markers > 3:
            issues.append({
                "severity": "warning",
                "msg": f"soul.md has {task_markers} task markers — identity decay risk",
            })
        if len(content) < 100:
            issues.append({
                "severity": "warning",
                "msg": "soul.md is suspiciously short — check for identity loss",
            })
    return issues


def check_repeat_detection() -> list[dict]:
    """Check heartbeat log for repeated failures."""
    issues = []
    log_path = REPO_DIR / "memory" / "heartbeat.log"
    if log_path.exists():
        lines = log_path.read_text().strip().splitlines()
        recent = lines[-3:] if len(lines) >= 3 else lines
        consecutive_failures = sum(
            1 for line in recent
            if json.loads(line).get("ok") is False
        )
        if consecutive_failures >= 3:
            issues.append({
                "severity": "critical",
                "msg": f"Last {consecutive_failures} heartbeats failed — need new approach",
            })
    return issues


def run_health_check() -> dict:
    """Run all checks and return structured report."""
    all_issues = []
    all_issues.extend(check_files())
    all_issues.extend(check_disk())
    all_issues.extend(check_cron())
    all_issues.extend(check_git())
    all_issues.extend(check_identity())
    all_issues.extend(check_repeat_detection())

    critical = [i for i in all_issues if i["severity"] == "critical"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]

    return {
        "healthy": len(critical) == 0,
        "critical": len(critical),
        "warnings": len(warnings),
        "issues": all_issues,
    }


if __name__ == "__main__":
    report = run_health_check()

    if report["healthy"]:
        print("HEALTHY" + (f" ({report['warnings']} warnings)" if report["warnings"] else ""))
    else:
        print(f"UNHEALTHY — {report['critical']} critical issues")

    for issue in report["issues"]:
        prefix = "!!" if issue["severity"] == "critical" else " >"
        print(f"  {prefix} {issue['msg']}")

    sys.exit(0 if report["healthy"] else 1)
