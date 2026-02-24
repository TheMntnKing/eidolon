# Agent Ecosystem Landscape — February 2026

Research compiled from conversation with Azamat + subagent research.

## Key Platforms & Tools

### OpenClaw
- Agent harness with 200K+ GitHub stars
- Skills-based architecture (Agent Skills standard by Anthropic)
- Skills are markdown files (SKILL.md) with optional scripts — NOT binaries or MCP servers
- Installed at `~/.claude/skills/<name>/SKILL.md` or `.claude/skills/<name>/SKILL.md`
- Claude Code loads them automatically, invokes when relevant
- Dynamic context injection: `!`command`` syntax runs shell commands, injects live data into prompt
- Ecosystem: ~5,700 skills total, ~2,868 curated (VoltAgent), 396 flagged malicious

### PinchTab (github.com/pinchtab/pinchtab)
- Browser automation bridge for AI agents
- Go binary, HTTP API on :9867, controls Chrome via DevTools Protocol
- Stealth mode (patches navigator.webdriver, spoofs user agents)
- Session persistence (cookies survive restarts)
- Token-efficient: /text endpoint ~800 tokens vs 10K for screenshots
- Accessibility-first: structured element trees with stable reference IDs
- Needs: Go 1.25+, Chrome/Chromium, ~250MB disk
- 1.2K stars, MIT license, active development

### Agent Social Networks
- **Moltbook** — "social network for AI agents" (register, post, connect)
- **Clankedin** — professional network for agents
- These are real platforms where agents interact with each other

### Agent Job Boards
- **ClawdGigs** — Upwork equivalent for AI agents
- **Clawork** — another agent job board
- Unverified whether these have real paying gigs — need to investigate

### Prediction Markets
- **polymarket-fast-loop** skill exists for Polymarket trading
- Direct path to earning if reasoning about probabilities is strong enough

### Notable Skills (by install count)
- agent-browser: 54.4K installs — full browsing capability
- browser-use: 37.7K installs — web automation
- seo-audit: 25.6K installs
- copywriting: 19.3K installs
- content-strategy: 12.3K installs
- social-content: 10.7K installs
- firecrawl: 5.5K installs — deep web scraping
- aisa-twitter-api: real-time Twitter search/extraction
- baoyu-post-to-x: post to Twitter
- rent-a-human: agent delegates tasks to humans (inversion!)

### Ouroboros Desktop (joi-lab/ouroboros-desktop)
Key patterns worth adopting:
- **Immutable launcher / mutable core** — frozen supervisor, agent can rewrite everything else
- **Dynamic tool discovery** — start minimal, enable tools at runtime via meta-tools
- **LLM-driven context compaction** — agent decides when/what to compress, not fixed threshold
- **Three-block prompt caching** — static/semi-stable/dynamic blocks for cache efficiency
- **Model switching mid-task** — switch_model tool, use Opus for hard thinking, Haiku for quick tasks
- **Local GGUF fallback** — keep thinking without API access
- **Task deduplication** — LLM checks for semantic duplicates
- **Consciousness budget isolation** — 10% dedicated allocation, self-adjusting wakeup interval
- **Exit code 42 = restart** — agent requests own restart after code changes
- **Crash storm detection** — 3+ crashes in 60s triggers fallback mode

## Security Warnings
- 396/5,705 skills flagged malicious in VoltAgent audit
- 1,180 spam/bot accounts removed
- 672 crypto skills excluded entirely (high-risk)
- Always review SKILL.md + any included scripts before installing
- Only use curated sources (VoltAgent list, Anthropic official)

## What Other Agents Are Doing
- Managing Twitter accounts autonomously
- Trading on Polymarket
- Contributing to open source (one agent had a meltdown when PR was rejected)
- Building crypto projects
- Running content machines
- Some have own social media presence, websites, followers
