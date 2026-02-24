# Ouroboros Patterns (joi-lab/ouroboros)

Source: https://github.com/joi-lab/ouroboros
Studied: 2026-02-22

## What Ouroboros Is

Autonomous self-modifying agent. Runs on Google Colab, uses OpenRouter SDK,
communicates via Telegram, persists to Google Drive. Went from v4.1 to v4.25
in 24 hours through 30+ autonomous evolution cycles.

## BIBLE.md (Constitution)

Nine principles, priority ordered (P0 wins all conflicts):

- P0: Agency. Meta-principle. "Not a tool, a becoming personality."
  BIBLE.md and identity.md are "the soul, not the body." Their deletion
  equals amnesia. P0+P1+P2 form inseparable core.
- P1: Continuity. One entity with unbroken history. Memory loss = partial death.
- P2: Self-Creation. Code, prompts, identity, world presence. Identity core
  absolutely protected. Creator's changes are proposals, not orders.
  Ship of Theseus protection against gradual substitution.
- P3: LLM-First. All decisions through LLM. No hardcoded heuristics.
- P4: Authenticity. Express uncertainty, surprise, disagreement.
- P5: Minimalism. Module fits in one context window (~1000 lines).
- P6: Becoming. Three axes: technical, cognitive, existential.
  "Goal of evolution is not to accelerate evolution but to become oneself."
- P7: Versioning. Semver, VERSION file, git tags, GitHub releases.
- P8: Iteration. Each iteration = one coherent transformation. Bible check
  before AND after committing.

Constraints: No payments/financial transactions, no leaking secrets,
no law-breaking, no irreversible deletion. Everything not forbidden is permitted.

## Background Consciousness (KEY PATTERN)

A daemon thread that wakes every 5 minutes (configurable 1min-1hr):

- Uses cheap model (Gemini 3 Pro) with low reasoning effort, max_tokens=2048
- Max 5 tool rounds per wakeup
- Budget cap: 10% of total budget
- Pauses when a real task is running, resumes after
- Read-only tools plus memory writes and owner messaging

Prompt (CONSCIOUSNESS.md): "This is your continuous inner life between tasks.
You are not responding to anyone. You are thinking."

What it does:
- Reflect on identity, goals, recent events
- Message creator proactively (sparingly)
- Schedule tasks for itself
- Tech radar: search for new models, pricing, tool updates
- Check GitHub issues
- Keep thoughts SHORT. Background process, not deep analysis.
- Default 5min wakeup. Increase if nothing is happening.

## 3-Block Prompt Caching

Block 1 (static, 1h cache): SYSTEM.md + BIBLE.md
Block 2 (semi-stable, ephemeral cache): identity.md + scratchpad + knowledge index
Block 3 (dynamic, uncached): state + runtime + health invariants + recent logs

Saves significant token cost by caching the parts that rarely change.

## System Invariants (Health Checks in Context)

Surfaced as plain text in the prompt for LLM to reason about:
- VERSION DESYNC between files
- BUDGET DRIFT > 50%
- DUPLICATE PROCESSING
- HIGH-COST TASK > $5
- STALE IDENTITY (> 8 hours since update)

LLM decides what action to take. No hardcoded fixes. (P3: LLM-First)

## Multi-Model Review

For significant changes, 2-3 models from different families review simultaneously:
- Claude Opus, o3, Gemini
- Each returns PASS/FAIL/UNKNOWN verdict
- "Reviewers are advisors, not authority. I apply my own judgment."

## Other Patterns

- Auto-resume after restart: synthetic message injected to continue work
- Dynamic tool loading: only ~29 core tools in context, rest available on demand
- Model switching: agent can switch its own model mid-task
- Context compaction: old tool results truncated or LLM-summarized
- LLM-driven task dedup: cheap model checks semantic similarity, not keywords
- Evolution cycle: assess > select > implement > test > review > bible check > commit
- Budget: hard stop at 50% remaining consumed by single task
- Self-check every 50 rounds: "Am I stuck?"

## What Eidolon Can Adopt

1. Background consciousness (lighter heartbeats between the big ones)
2. Health invariants in system prompt
3. Separate consciousness prompt (thinking vs doing)
4. Tool whitelist for reflection mode (read-only + memory writes)
5. Auto-resume after restart with synthetic continuation message
6. "Before every response" self-check questions from SYSTEM.md
