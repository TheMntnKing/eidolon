# Tool Selection Guide
Researched: 2026-02-24
Sources: Empirical testing + conversation with Azamat
Confidence: high

## Reading content from URLs

**Default: markdown-fetch** (`curl https://markdown.new/{url}`)
- Works for static HTML and SSR'd SPAs (Next.js, Nuxt, React w/ SSR)
- 80% fewer tokens than raw HTML, ~0.1–1.5s, no auth
- `method=browser` (POST) for pure client-side JS — but can fail on anti-bot sites
- `method=ai` returns JSON with token count metadata (same content)

Decision: try markdown-fetch first. Fall back to pinchtab only if it returns empty/error.

## Browser interaction

**Use: pinchtab-browser skill**
- Accessibility tree snapshots (e0, e1... refs), ~800–1500 tokens for interactive elements
- Headless (port 9867): autonomous, runs 24/7
- Supervised (port 9868): Azamat's desktop Chrome via SSH tunnel — for 2FA, acting as him

## When NOT to use a browser at all

- Reading docs, articles, blog posts → markdown-fetch
- Calling APIs with known endpoints → curl directly
- GitHub data → gh CLI (when authenticated)

## Decision tree

```
Need to read a URL?
  → markdown-fetch (default)
  → If empty/error: pinchtab headless

Need to interact (click, fill, submit)?
  → pinchtab headless

Need Azamat's session / 2FA?
  → pinchtab supervised mode

Need API data with a clean endpoint?
  → curl directly

Markdown.new blocked by Cloudflare?
  → WebFetch (Anthropic-side fetch, different IP)
```

## Token cost comparison

| Method | Typical tokens |
|--------|---------------|
| markdown-fetch | ~500–3,000 |
| WebFetch | ~1,000–5,000 |
| pinchtab snap (interactive) | ~800–1,500 |
| pinchtab snap (full) | ~10,000+ |
| pinchtab get text | ~800 |
| Raw HTML | ~5,000–50,000+ |

## What's redundant / deprecated

- **agent-browser**: redundant with pinchtab. Has `--auto-connect` for CDP but untested.
  More features (state persistence, video, mobile) but nothing we need.
  NPX dependency, slower startup. Not worth maintaining two browser tools.
- **WebFetch**: still useful as fallback when markdown.new is blocked. Not primary.
- **tools/start-browser.sh**: DELETED. Use `.claude/skills/pinchtab-browser/scripts/start.sh`.

## Skill file format (Claude Code / OpenClaw)

Valid frontmatter fields: `name`, `description`, `argument-hint`, `compatibility`,
`disable-model-invocation`, `license`, `metadata`, `user-invokable`

NOT valid: `allowed-tools` (causes parse error)

`description` must be single-line string — no multiline YAML (`description: >` breaks it)
