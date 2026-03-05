---
name: cdp-browser-automation
description: Automate Chrome via Chrome DevTools Protocol (CDP) for browser tasks like logging into websites, filling forms, clicking buttons, scraping content, and navigating SPAs. Use when you need to interact with a website that requires JavaScript, authentication, or browser rendering — including login flows, dashboards, web apps, and any site where curl/requests won't work. Requires Chrome installed on the host.
---

# CDP Browser Automation

Automate Chrome using the Chrome DevTools Protocol (CDP) via Python websockets.

## Setup

### Launch Chrome with remote debugging
```bash
pkill -a "Google Chrome" 2>/dev/null
sleep 1
open -a "Google Chrome" --args --remote-debugging-port=18800 --user-data-dir=/tmp/chrome-debug
sleep 3
# Verify
curl -s http://localhost:18800/json/version | python3 -c "import json,sys; print(json.load(sys.stdin).get('Browser','FAIL'))"
```

### Python requirements
Use `/opt/homebrew/bin/python3.12` — `websockets` is installed there.
```bash
# Install if missing
/opt/homebrew/bin/python3.12 -m pip install websockets --break-system-packages -q
```

## Core Pattern

```python
import asyncio, websockets, json, urllib.request

def get_browser_ws():
    data = json.loads(urllib.request.urlopen("http://localhost:18800/json/version").read())
    return data['webSocketDebuggerUrl']

async def send_cmd(ws, method, params, msg_id):
    await ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
    for _ in range(50):
        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
        if resp.get('id') == msg_id:
            return resp
    return None

async def evaluate(ws, expr, msg_id):
    return await send_cmd(ws, "Runtime.evaluate", {"expression": expr, "awaitPromise": True}, msg_id)

async def click(ws, x, y, mid):
    await send_cmd(ws, "Input.dispatchMouseEvent", {"type":"mousePressed","x":x,"y":y,"button":"left","clickCount":1}, mid)
    await send_cmd(ws, "Input.dispatchMouseEvent", {"type":"mouseReleased","x":x,"y":y,"button":"left","clickCount":1}, mid+1)
```

## Common Operations

### Open a new tab and navigate
```python
bws = get_browser_ws()
async with websockets.connect(bws) as ws:
    await ws.send(json.dumps({"id":1,"method":"Target.createTarget","params":{"url":"https://example.com"}}))
    resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
    target_id = resp['result']['targetId']

ws_url = f"ws://localhost:18800/devtools/page/{target_id}"
async with websockets.connect(ws_url) as ws:
    await asyncio.sleep(3)
    r = await evaluate(ws, "document.title", 1)
    print(r['result']['result']['value'])
```

### Fill a form and submit
```python
# Works for React/SPA — dispatches input+change events
await evaluate(ws, """
    (function() {
        const el = document.querySelector('input[name="email"]');
        el.focus();
        el.value = 'user@example.com';
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        return 'filled';
    })()
""", 2)

# Click button by label text
r = await evaluate(ws, """
    (function() {
        const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Sign in');
        const rect = btn.getBoundingClientRect();
        return JSON.stringify({x: rect.x + rect.width/2, y: rect.y + rect.height/2});
    })()
""", 3)
pos = json.loads(r['result']['result']['value'])
await click(ws, pos['x'], pos['y'], 4)
await asyncio.sleep(4)
```

### Scrape page content
```python
r = await evaluate(ws, """
    JSON.stringify({
        title: document.title,
        url: window.location.href,
        text: document.body.innerText.slice(0, 3000),
        links: Array.from(document.querySelectorAll('a')).map(a => ({text: a.textContent.trim(), href: a.href}))
    })
""", 5)
data = json.loads(r['result']['result']['value'])
```

### Navigate existing tab
```python
await send_cmd(ws, "Page.navigate", {"url": "https://example.com"}, 1)
await asyncio.sleep(4)
```

## Key Rules

1. **`Target.createTarget` via browser WS** — not `/json/new` (shell escaping breaks it)
2. **CDP mouse clicks > JS `.click()`** — `Input.dispatchMouseEvent` (mousePressed + mouseReleased) is more reliable for SPAs
3. **React/SPA forms** need both `input` and `change` events with `{bubbles:true}`
4. **Wait after navigation** — `await asyncio.sleep(3)` before interacting
5. **Match response by id** — always check `resp.get('id') == msg_id`
6. **Use `/opt/homebrew/bin/python3.12`** — system python3 lacks websockets

## Troubleshooting

- **Connection refused on 18800**: Chrome not running with debug flag — re-run launch command
- **WS connection closed**: Page navigated; reconnect using new tab's WS URL
- **Form not submitting**: Try `form.submit()` fallback; for SPAs with no `<form>` tag, rely solely on button click
- **Element not found**: Page still loading — increase sleep time
- **`NoneType` errors from send_cmd**: Increase retry count or timeout in `send_cmd`
