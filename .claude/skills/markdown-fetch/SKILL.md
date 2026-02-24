---
name: markdown-fetch
description: Convert any URL to clean Markdown using markdown.new (Cloudflare-powered). Default method works for static HTML and SSR'd SPAs. Use method=browser for pure client-side JS. Much cheaper than a real browser for read-only tasks. Use pinchtab only when you need to interact with the page.
---

# markdown-fetch

Converts any URL to clean Markdown. Cloudflare fetches the page server-side
and returns structured Markdown — no browser needed for most sites.

## Core usage

```bash
# Default (auto) — works for most sites including SSR'd SPAs
curl -sL https://markdown.new/https://example.com

# Via wrapper script (with optional line limit)
.claude/skills/markdown-fetch/scripts/fetch.sh https://example.com
.claude/skills/markdown-fetch/scripts/fetch.sh https://example.com 100

# Browser rendering — for pure client-side JS apps (method=browser)
# NOTE: can fail on sites with strong anti-bot (returns error JSON if blocked)
curl -s 'https://markdown.new/' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com", "method": "browser"}'

# URL query parameter form (same as POST method=browser)
curl -sL 'https://markdown.new/https://example.com?method=browser'

# AI method — same content as auto, but returns JSON envelope with metadata
curl -s 'https://markdown.new/' \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com", "method": "ai"}'

# Retain images in output
curl -sL 'https://markdown.new/https://example.com?retain_images=true'
```

## Conversion methods

| Method | How | Use when |
|--------|-----|----------|
| `auto` (default) | Cloudflare fetch + Workers AI | Default. Works for static HTML + SSR'd SPAs |
| `browser` | Headless browser rendering | Pure client-side JS apps that SSR can't handle. Can fail on anti-bot sites. |
| `ai` | Same as auto, JSON response | When you want metadata (token count, duration_ms) with the content |

## When to use this vs alternatives

| Need | Tool |
|------|------|
| Read content from a URL (default choice) | **markdown-fetch** ← start here |
| SSR'd SPA (Next.js, Nuxt, React w/ SSR) | **markdown-fetch** auto works |
| Pure client-side SPA where auto fails | **markdown-fetch** method=browser |
| Interact with a page (click, fill forms) | pinchtab-browser |
| Need login / session / Azamat's account | pinchtab supervised mode |
| markdown.new returns error/empty | WebFetch or pinchtab fallback |

## Properties

- **Token efficiency**: ~80% fewer tokens than raw HTML
- **Speed**: 0.1–0.6s (auto/ai), 1–5s (browser)
- **Auth**: None required
- **Network**: Cloudflare fetches the URL — not the VM
- **JS execution**: auto=no, browser=yes (when it works)

## Output format (auto/browser)

Returns structured Markdown:
```
Title: Page Title

URL Source: https://original-url.com

Markdown Content:
[actual page content in markdown]
```

Output format (ai method):
```json
{"success": true, "url": "...", "title": "...", "content": "...",
 "method": "ai", "duration_ms": 0, "tokens": 7225}
```

## Limitations

- `browser` method can fail on sites with strong bot protection (returns error JSON)
- Pure client-side SPAs with no SSR may still need pinchtab even with method=browser
- Some sites block Cloudflare's fetch IPs entirely — fallback to pinchtab
- Large pages can be verbose — use `head -n N` or max_lines arg to limit output
- No cookie/session support — use pinchtab for auth-gated content

## Token cost guide

| Approach | Typical tokens |
|----------|---------------|
| markdown-fetch (this tool) | ~500–3,000 |
| WebFetch (built-in) | ~1,000–5,000 |
| pinchtab snap (interactive) | ~800–1,500 |
| pinchtab get text | ~800 |
| Raw HTML | ~5,000–50,000+ |
