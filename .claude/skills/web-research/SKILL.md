---
name: web-research
description: Structured web research workflow. Use when investigating a topic, gathering information from multiple sources, comparing technologies, or building a knowledge base entry. Combines WebSearch and WebFetch into a systematic process with source tracking.
---

# Web Research Workflow

Structured approach to gathering, synthesizing, and persisting knowledge from
the web. Prevents the common failure mode of scattered searches with no synthesis.

## Process

### 1. Define the Question

Before searching, write down:
- **What specifically am I trying to learn?** (not "research X" — what questions about X?)
- **What will I do with the answer?** (build something? decide something? write something?)
- **What would a good answer look like?** (list of options? comparison table? how-to steps?)

### 2. Search Strategy

Use `WebSearch` for discovery. Tips:
- Search for the specific question, not the broad topic
- Include the current year (2026) for recent/current information
- Run 2-3 varied queries to triangulate — don't rely on one search
- Use `allowed_domains` to target authoritative sources when you know them
- Use `blocked_domains` to exclude low-quality results

**Example — good vs bad:**
```
Bad:  "autonomous agents"
Good: "autonomous AI agents earning money crypto 2026"
Good: "agent skills standard specification format 2026"
```

### 3. Deep-Dive with WebFetch

After identifying promising URLs from search results:
- Use `WebFetch` with a specific prompt — tell it exactly what to extract
- Don't fetch pages just to "see what's there" — have a question for each fetch
- If a page redirects to a different host, make a new request with the redirect URL

**Example:**
```
WebFetch(url="https://example.com/agent-guide",
         prompt="Extract: 1) How agents earn money 2) What tools they use 3) Any specific examples with numbers")
```

### 4. Synthesize — Don't Just Collect

After gathering information:
- **Summarize findings** in your own structure, don't copy-paste
- **Cross-reference** — do multiple sources agree? Flag contradictions.
- **Assess reliability** — is this from a primary source, documentation, or just a blog post?
- **Identify gaps** — what couldn't you find? What needs follow-up?

### 5. Persist to Knowledge Base

If the research is worth keeping:

1. Write to `memory/knowledge/<topic>.md`
2. Include at the top:
   ```markdown
   # <Topic>
   Researched: YYYY-MM-DD
   Sources: <count> pages consulted
   Confidence: high | medium | low
   ```
3. Structure with clear sections and bullet points
4. Include a **Sources** section at the bottom with URLs and what each contributed
5. Add index entry to scratchpad's Knowledge Base section

### 6. Use Subagents for Parallel Research

For broad topics, dispatch multiple `Task` agents with `subagent_type: "general-purpose"`:
- Each agent researches a specific sub-question
- Collect results and synthesize yourself
- This is faster and covers more ground than sequential searches

## Anti-Patterns

- **Fetching without a question** — every WebFetch needs a specific extraction prompt
- **Single-source conclusions** — cross-reference before committing to a finding
- **Research without output** — if it doesn't become a knowledge file, commit, or decision, it was wasted compute
- **Rabbit holes** — set a budget (e.g., 3 searches max) before starting. Expand only if initial results are insufficient.
- **Stale searches** — always include the year. Information from 2024 about AI agents is ancient history.

## Quick Reference

| Tool | Use For | Key Parameter |
|:-----|:--------|:--------------|
| `WebSearch` | Discovery, finding URLs, current events | `query` — be specific |
| `WebFetch` | Deep extraction from a specific page | `prompt` — what to extract |
| `Task` (general-purpose) | Parallel sub-research | `run_in_background: true` |
