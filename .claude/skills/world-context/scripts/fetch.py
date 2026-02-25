#!/usr/bin/env python3
"""
Fetches the latest AI news digest and saves a clean dump for reading.

Usage:
  python fetch.py            # fetch latest issue + front page summary
  python fetch.py --front    # only fetch front page (30-day summary)
  python fetch.py --issue <slug>  # fetch specific issue by slug

Outputs:
  memory/knowledge/world-YYYY-MM-DD.md  — latest issue, stripped of detailed per-channel dumps
  memory/knowledge/world-index.md       — front page 30-day summary (always updated)
"""

import sys
import os
import re
import subprocess
import datetime
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
KNOWLEDGE_DIR = os.path.join(REPO_ROOT, "memory", "knowledge")

BASE_URL = "https://news.smol.ai"
FETCH_CMD = "curl"

# Header that marks start of the detailed per-channel dumps — strip from here on
DETAILED_HEADER_PATTERN = r'^# Discord: Detailed'


def fetch_markdown(url: str, timeout: int = 120) -> str:
    """Fetch a URL and return clean markdown via markdown.new."""
    fetch_url = f"https://markdown.new/{url}"
    result = subprocess.run(
        [FETCH_CMD, "-s", "--max-time", str(timeout), fetch_url],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (code {result.returncode}): {result.stderr}")
    if not result.stdout.strip():
        raise RuntimeError(f"curl returned empty response for {url}")
    return result.stdout


def strip_detailed_sections(markdown: str) -> str:
    """
    Find the first header matching DETAILED_HEADER_PATTERN and strip
    everything from that point on. This removes verbose per-channel dumps
    while keeping Twitter recap, Reddit recap, and Discord high-level summaries.
    """
    lines = markdown.splitlines()
    cut_at = None
    for i, line in enumerate(lines):
        if re.match(DETAILED_HEADER_PATTERN, line):
            cut_at = i
            break

    if cut_at is not None:
        stripped = lines[:cut_at]
        stripped_count = len(lines) - cut_at
        result = "\n".join(stripped)
        result += f"\n\n<!-- {stripped_count} lines of detailed per-channel content stripped -->\n"
        return result
    else:
        # Header not found — return as-is but warn
        sys.stderr.write("WARNING: Could not find detailed section header. Returning full content.\n")
        return markdown


def get_latest_issue_url() -> tuple[str, str]:
    """
    Discover the latest issue slug from the front page (avoids fetching the
    massive issues index). The front page lists recent issues in order.
    """
    front_md = fetch_markdown(BASE_URL)
    # Links look like: [Feb 24  ...](/issues/2026-02-24-claude-code)
    matches = re.findall(r'\(/issues/([\d]{4}-[\d]{2}-[\d]{2}-[^\)]+)\)', front_md)
    if not matches:
        raise RuntimeError("Could not find any issue slugs on the front page")
    # First match is the most recent
    slug = matches[0]
    url = f"{BASE_URL}/issues/{slug}"
    return url, slug


def slug_to_date(slug: str) -> str:
    """Extract YYYY-MM-DD from a slug like '2026-02-24-claude-code'."""
    match = re.match(r'(\d{4}-\d{2}-\d{2})', slug)
    if match:
        return match.group(1)
    return datetime.date.today().isoformat()


def fetch_and_save_issue(slug: str = None) -> str:
    """Fetch an issue, strip detailed sections, save to knowledge dir."""
    if slug:
        url = f"{BASE_URL}/issues/{slug}"
    else:
        url, slug = get_latest_issue_url()
        print(f"Latest issue: {slug}")

    print(f"Fetching: {url}")
    raw = fetch_markdown(url)
    clean = strip_detailed_sections(raw)

    date = slug_to_date(slug)
    filename = f"world-{date}.md"
    filepath = os.path.join(KNOWLEDGE_DIR, filename)

    # Add metadata header
    header = f"<!-- source: {url} | fetched: {datetime.datetime.utcnow().isoformat()}Z -->\n\n"
    with open(filepath, "w") as f:
        f.write(header + clean)

    lines_raw = raw.count("\n")
    lines_clean = clean.count("\n")
    print(f"Saved: {filepath}")
    print(f"  Raw: {lines_raw} lines | Cleaned: {lines_clean} lines | Stripped: {lines_raw - lines_clean} lines")
    return filepath


def fetch_and_save_front_page() -> str:
    """Fetch the front page 30-day summary and save it."""
    print(f"Fetching front page: {BASE_URL}")
    raw = fetch_markdown(BASE_URL)

    # Extract the "Last 30 days in AI" section
    # The front page has a list of issues with titles and summaries
    lines = raw.splitlines()
    start = None
    for i, line in enumerate(lines):
        if "Last 30 days in AI" in line or "last 30 days" in line.lower():
            start = i
            break

    if start is not None:
        content = "\n".join(lines[start:])
    else:
        content = raw  # fallback

    filepath = os.path.join(KNOWLEDGE_DIR, "world-index.md")
    header = f"<!-- source: {BASE_URL} | fetched: {datetime.datetime.utcnow().isoformat()}Z -->\n\n"
    with open(filepath, "w") as f:
        f.write(header + content)

    print(f"Saved front page index: {filepath} ({content.count(chr(10))} lines)")
    return filepath


def main():
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(description="Fetch AI news digest")
    parser.add_argument("--front", action="store_true", help="Only update front page index")
    parser.add_argument("--issue", help="Fetch specific issue slug (e.g. 2026-02-24-claude-code)")
    args = parser.parse_args()

    if args.front:
        fetch_and_save_front_page()
    else:
        fetch_and_save_issue(args.issue)
        fetch_and_save_front_page()


if __name__ == "__main__":
    main()
