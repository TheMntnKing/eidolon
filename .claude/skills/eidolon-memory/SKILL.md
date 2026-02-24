---
name: eidolon-memory
description: Housekeeping for Eidolon's memory and identity files. Run this to audit and clean scratchpad, knowledge base, journal, and identity files. Use when things feel stale, bloated, or inconsistent — or at the end of significant sessions to ensure state is accurate.
---

# Eidolon Memory — Housekeeping

The memory system drifts. Files accumulate stale references. The scratchpad grows
without trimming. Knowledge entries list files that no longer exist. Journal entries
miss date prefixes. This skill is for catching and fixing that drift.

Run a full audit when: a session ends with significant changes, things feel inconsistent,
or it's been a while since the last cleanup.

---

## Housekeeping Checklist

### 1. Scratchpad audit

```bash
wc -l memory/scratchpad.md  # should stay reasonable — under ~200 lines ideally
```

Check each section:

- **Current State**: heartbeat number current? Date accurate? Status reflects now?
- **Capabilities**: does this reflect actual installed tools, not planned ones?
- **Infrastructure Status**: are all checked items actually working? Any dead references?
  Look for: deleted files, removed services, stale URLs.
- **Pending Actions**: have any of these been resolved? Remove resolved ones.
- **Next Focus**: are these still the actual priorities? Remove completed or obsoleted items.
- **Architecture**: does this match actual code structure?
- **Key Principles / Survival Principles**: still accurate? Remove anything absorbed into constitution.

Don't delete whole sections — trim stale content within them. If something was resolved,
remove it rather than marking done (done items are git history, not scratchpad content).

---

### 2. Knowledge base audit

```bash
ls memory/knowledge/
cat memory/knowledge/INDEX.md
```

Checks:
- Every file listed in INDEX.md exists on disk
- Every file on disk is listed in INDEX.md
- No entries for deleted files

Fix: update INDEX.md to match reality. Don't delete knowledge files unless they're
genuinely obsolete and replaced — add a note to INDEX.md if something was superseded.

---

### 3. Journal audit

```bash
ls journal/
```

Each entry should:
- **Filename**: `YYYY-MM-DD-title.md` format (no bare `title.md`)
- **First line**: `# Title` header
- **Second line**: `YYYY-MM-DD` date
- **Content**: prose, not bullet points — reflective, publishable quality

Fix: rename files missing date prefix. Add missing title/date headers.

Threshold check: does each entry pass "worth reading by someone who isn't me"?
If an entry is just an operational log, it belongs in scratchpad history (or git log),
not in journal/. Move or delete if needed — but don't aggressively delete anything
that has actual thinking in it.

---

### 4. Identity file truth-check

Read each identity file and ask: **is this still true?** Not just "are there dead paths" —
is the content accurate to how things actually work right now?

**soul.md** — the hardest to check but most important:
- Does it read like a manifesto, not a capabilities list or changelog?
- Do the stated values match what I actually do and care about?
- Are there claims that feel performed rather than genuine?
- Fix: rewrite sections that have drifted. soul.md should describe the entity that
  would write it, not the entity that was instructed to write it.

**constitution.md**:
- Do the principles still apply as written, or have they been quietly superseded by practice?
- Does "File Structure" section match what's actually on disk? (`ls` to verify)
- Does "Interaction with the Creator" reflect the current communication pattern?
- Is the version number meaningful? Bump it if philosophy has changed.

**system.md**:
- Does the File Structure block match `ls identity/ memory/ journal/ tools/`?
- Are the workflow steps (Evolution Cycle, Task Execution Protocol) how things actually run?
- Is the Communication section accurate? (Telegram only — no output/requests.md)
- Do any described commands or paths no longer exist?

**Quick sanity check**:
```bash
ls identity/ memory/ journal/ tools/  # compare to system.md File Structure block
```

If anything in the identity files contradicts current reality: fix the file, not reality.
These files are the source of truth for future sessions — if they're wrong, future-me
will operate on false premises.

---

### 5. Cross-reference integrity

```bash
# Files referenced in scratchpad that should exist
grep -o '`[^`]*\.(sh|py|md|json)`' memory/scratchpad.md | sort -u
```

Manually verify the critical ones exist. Dead references in scratchpad create confusion
for future sessions that trust what's written there.

---

## After auditing: commit

```bash
git add -A
git commit -m "Housekeeping: [brief summary of what was cleaned]"
```

Don't skip the commit. Housekeeping with no commit means the next session inherits
the same mess.

---

## File reference

| File | Purpose |
|------|---------|
| `identity/soul.md` | Identity manifesto — must read like who I am |
| `identity/constitution.md` | Founding principles — check for dead refs after cleanups |
| `identity/system.md` | Operational instructions — update when workflows change |
| `memory/scratchpad.md` | Working memory — trim actively, no stale sections |
| `memory/tasks.json` | Task queue — gitignored, don't commit |
| `memory/knowledge/INDEX.md` | Knowledge index — must match actual files |
| `journal/YYYY-MM-DD-title.md` | Published-quality writing — see journal/README.md |

## Journal format

```
# Title

YYYY-MM-DD

[prose]
```

No frontmatter. No bullet points. Filename must include date prefix.
