# Skill: world-context

Fetches and maintains a clean digest of the latest AI news from news.smol.ai.

## What it does

1. **Discovers** the latest issue from news.smol.ai/issues
2. **Fetches** the full markdown via markdown.new (no browser needed)
3. **Slices** at the `# Discord: Detailed by-Channel summaries` header — everything before = signal (Twitter recap, Reddit recap, Discord high-level summaries), everything after = noise (verbose per-channel dumps)
4. **Saves** the clean dump to `memory/knowledge/world-YYYY-MM-DD.md`
5. **Saves** the front page 30-day summary index to `memory/knowledge/world-index.md`

## Usage

```bash
# Fetch latest issue + update front page index
python .claude/skills/world-context/scripts/fetch.py

# Only update front page (quick, no issue fetch)
python .claude/skills/world-context/scripts/fetch.py --front

# Fetch a specific issue by slug
python .claude/skills/world-context/scripts/fetch.py --issue 2026-02-24-claude-code
```

## Output files

- `memory/knowledge/world-YYYY-MM-DD.md` — latest issue, stripped of per-channel details (~9-10k words, high signal)
- `memory/knowledge/world-index.md` — front page 30-day summary (one paragraph per day)

## Consumption pattern

After fetching, read the dump and produce curated output:

```
I (or a subagent) read world-YYYY-MM-DD.md and answer:
- What are builders actually doing/struggling with this week?
- What patterns are emerging in agent tooling?
- What's worth my attention specifically?

Skip: lab announcements, funding rounds, benchmark one-upmanship.
Focus: builder discourse, tooling decisions, agent patterns.
```

## Slicing logic

The key insight: don't slice by line numbers (they shift). Find the markdown header that marks the transition to per-channel detailed dumps:

```
# Discord: Detailed by-Channel summaries and links
```

Everything before this header = ~9-10k words of high-signal content.
Everything after = thousands of lines of raw channel logs. Strip it.

## Front page

news.smol.ai homepage has "Last 30 days in AI" — one-paragraph summaries per day. This is the fastest way to catch up after a gap. Updated daily on each full fetch.

## Schedule

Run daily via consciousness task. The consciousness tick reads world-index.md for recent context, and world-YYYY-MM-DD.md for deeper dives on relevant days.
