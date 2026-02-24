---
name: pinchtab-browser
description: Control a Chrome browser for web automation. Headless mode (port 9867) for autonomous work; supervised mode (port 9868) to control Azamat's visible desktop Chrome. Use when clicking elements, filling forms, or any multi-step web workflow that requires interaction. Exposes the accessibility tree as stable element refs (e0, e1...) for token-efficient interaction.
---

# pinchtab-browser

Two modes:
- **Headless** (port 9867): my Chrome on the VM, runs autonomously 24/7
- **Supervised** (port 9868): Azamat's visible desktop Chrome via SSH tunnel — for acting as him, 2FA, CAPTCHAs

All browser operations go through `./scripts/browse.sh`.

## Setup — Headless Mode (autonomous)

Start the server first — required before any browser work:

```bash
./scripts/start.sh
# PinchTab PID: 12345
# PinchTab ready on port 9867
```

Verify:
```bash
./scripts/browse.sh health
# {"status": "ok", "tabs": 3}
```

## Setup — Supervised Mode (Azamat's desktop Chrome)

**Azamat's steps** (on his machine):
1. Start Chrome with debug port:
   ```bash
   google-chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-remote-debug
   ```
2. Establish SSH reverse tunnel (with keepalive):
   ```bash
   ssh -o ServerAliveInterval=30 -J azamat@<JUMP_HOST> -R 9222:localhost:9222 eidolon@<VM_IP>
   ```
   The `-o ServerAliveInterval=30` is required — without it the tunnel drops after ~2min idle.
3. Tell Eidolon "supervised mode ready"

**Eidolon then runs:**
```bash
./scripts/start-supervised.sh
# Chrome found. CDP URL: ws://localhost:9222/...
# Supervised PinchTab ready on port 9868
```

**Interact via supervised mode:**
```bash
BRIDGE_PORT=9868 ./scripts/browse.sh nav https://example.com
BRIDGE_PORT=9868 ./scripts/browse.sh snap
```

**Stop supervised mode:**
```bash
./scripts/stop-supervised.sh
```

The headless instance (port 9867) keeps running throughout — supervised mode is additive, not a replacement.

**Known quirks:**
- `BRIDGE_NO_RESTORE=true` is required on headless startup — without it, Chrome fails with SingletonLock permission errors after an unclean shutdown
- Must use `/home/eidolon/.pinchtab/bin/pinchtab` directly — the `pinchtab nav`, `pinchtab snap` etc. CLI subcommands are on the `main` branch but NOT in the v0.6.3 release binary. The binary always starts a new server, never acts as a client. `browse.sh` wraps the HTTP API instead.
- Chrome binary must be `/opt/google/chrome/google-chrome` — the `chromium-browser` in PATH is a snap wrapper with AppArmor restrictions that prevent headless use
- **Supervised mode: CDP idle timeout** — the PinchTab→Chrome WebSocket goes through the SSH tunnel and drops if idle. `start-supervised.sh` runs a background keepalive (health ping every 30s) to prevent this. The SSH command also needs `-o ServerAliveInterval=30`.
- **Supervised mode: tab targeting** — PinchTab defaults to the first tab. When multiple tabs are open, get IDs via `BRIDGE_PORT=9868 ./scripts/browse.sh tabs` and pass `?tabId=<id>` directly to the API for specific-tab operations.
- **browse.sh timeouts** — all curl calls use `--max-time ${BROWSE_TIMEOUT:-30}`. For slow pages or long form submissions, set `BROWSE_TIMEOUT=60` before calling.

## Core Workflow

The accessibility tree loop — most token-efficient approach:

```
1. start server         → ./scripts/start.sh
2. navigate             → ./scripts/browse.sh nav <url>
3. snapshot             → ./scripts/browse.sh snap
   (get refs: e0, e1, e2...)
4. act on refs          → ./scripts/browse.sh click e5
5. snapshot diff        → ./scripts/browse.sh snap diff
   (see only what changed)
6. repeat from 4
```

Refs (e0, e1, e2...) are stable element references cached per tab after each snapshot. You don't need to re-snapshot before every action — only when the page has changed significantly (navigation, modal open/close, dynamic content loading).

## browse.sh — Full Command Reference

### Navigation
```bash
./scripts/browse.sh nav https://example.com
# {"title": "Example Domain", "url": "https://example.com/"}
```

### Snapshots (accessibility tree)
```bash
# Compact interactive elements only — start here, lowest token cost
./scripts/browse.sh snap
# e0:link "Learn more"
# e1:button "Search"
# e2:textbox "q"

# Full accessibility tree — use when mapping entire page structure
./scripts/browse.sh snap full

# Diff only — use after an action to see what changed
./scripts/browse.sh snap diff
```

### Clicking and interaction
```bash
./scripts/browse.sh click e0          # click element by ref
./scripts/browse.sh hover e3          # hover over element (triggers dropdowns, tooltips)
./scripts/browse.sh focus e5          # focus element without clicking
./scripts/browse.sh scroll e10        # scroll element into view
```

### Text input
```bash
./scripts/browse.sh type e2 "hello world"   # type text into ref (appends)
./scripts/browse.sh fill e2 "search term"   # fill field (clears first, then types)
./scripts/browse.sh press Enter             # press a key (Enter, Tab, Escape, ArrowDown, etc.)
./scripts/browse.sh select e6 "Option A"    # select a dropdown option by visible text
```

### Content extraction
```bash
./scripts/browse.sh text              # all visible page text (~800 tokens)
./scripts/browse.sh eval "document.title"          # run arbitrary JavaScript
./scripts/browse.sh eval "window.location.href"    # get current URL via JS
./scripts/browse.sh eval "document.querySelectorAll('a').length"  # count links
```

### Screenshot
```bash
./scripts/browse.sh ss                     # screenshot → /tmp/screenshot.jpg
./scripts/browse.sh ss /tmp/page.jpg       # screenshot to custom path
```

### Tab management
```bash
./scripts/browse.sh tabs
# {"tabs": [
#   {"id": "ABC123", "title": "Example Domain", "url": "https://example.com/"},
#   {"id": "DEF456", "title": "GitHub", "url": "https://github.com/"}
# ]}
```

## Multi-tab Workflows

When working with multiple tabs, pass `?tabId=<id>` to the HTTP API directly. Get the ID from `./scripts/browse.sh tabs`, then:

```bash
# Snapshot a specific tab (not the active one)
curl -s -H "Authorization: Bearer eidolon-bridge-secret" \
  "http://localhost:9867/snapshot?tabId=ABC123&filter=interactive&format=compact"

# Get text from a specific tab
curl -s -H "Authorization: Bearer eidolon-bridge-secret" \
  "http://localhost:9867/text?tabId=ABC123"

# Navigate a specific tab
curl -s -X POST http://localhost:9867/navigate \
  -H "Authorization: Bearer eidolon-bridge-secret" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "tabId": "ABC123"}'
```

## Token Cost Guide

| Command | Approximate tokens |
|---|---|
| `snap` (interactive + compact) | ~800–1,500 |
| `snap diff` | ~100–500 (only changes) |
| `snap full` | ~10,500 |
| `text` | ~800 |
| `ss` (screenshot) | ~2,000 (vision tokens) |

**Strategy**: always start with `snap`. After actions, use `snap diff` to check results. Only use `snap full` when you need the complete page structure. Use `text` when you just need to read content without interacting.

## Example: Search GitHub

```bash
./scripts/start.sh

./scripts/browse.sh nav https://github.com
./scripts/browse.sh snap
# e0:link "Sign in"
# e1:link "Sign up"
# e2:combobox "Search or jump to..."

./scripts/browse.sh click e2
./scripts/browse.sh snap diff
# e3:textbox "Search GitHub" *focused*

./scripts/browse.sh type e3 "pinchtab"
./scripts/browse.sh press Enter

./scripts/browse.sh snap diff
./scripts/browse.sh text
```

## Example: Fill a Login Form

```bash
./scripts/browse.sh nav https://example.com/login
./scripts/browse.sh snap
# e0:textbox "Email"
# e1:textbox "Password"
# e2:button "Sign in"

./scripts/browse.sh fill e0 "user@example.com"
./scripts/browse.sh fill e1 "mypassword"
./scripts/browse.sh click e2

./scripts/browse.sh snap diff   # check for error messages or redirect
./scripts/browse.sh text        # read page content after login
```

## Supporting files

- [`./scripts/start.sh`](./scripts/start.sh) — start headless PinchTab (port 9867)
- [`./scripts/stop.sh`](./scripts/stop.sh) — stop headless instance
- [`./scripts/start-supervised.sh`](./scripts/start-supervised.sh) — start supervised PinchTab (port 9868, Azamat's Chrome)
- [`./scripts/stop-supervised.sh`](./scripts/stop-supervised.sh) — stop supervised instance
- [`./scripts/browse.sh`](./scripts/browse.sh) — CLI wrapper for all browser operations (use `BRIDGE_PORT=9868` for supervised)
