"""openai-mcp setup wizard — one command, done."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# ── colours ────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def info(msg):
    print(f"  {YELLOW}→{RESET} {msg}")


def err(msg):
    print(f"  {RED}✗{RESET} {msg}")


def h1(msg):
    print(f"\n{BOLD}{msg}{RESET}")


# ── token acquisition ───────────────────────────────────────────────────────


def _token_from_codex() -> str | None:
    p = Path.home() / ".codex" / "auth.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        return d.get("accessToken") or d.get("access_token")
    except Exception:
        return None


def _token_from_saved() -> str | None:
    p = Path.home() / ".openai-mcp" / "token.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        return d.get("access_token")
    except Exception:
        return None


def _token_via_browser_use() -> str | None:
    """Use browser-use CLI to automate token extraction."""
    if not shutil.which("browser-use") and not shutil.which("bu"):
        return None
    cli = shutil.which("browser-use") or "bu"
    try:
        info("Connecting to browser...")
        subprocess.run(
            [cli, "open", "https://chat.openai.com"], timeout=20, check=False
        )
        time.sleep(4)

        # Try Auth0 localStorage
        r = subprocess.run(
            [
                cli,
                "eval",
                "JSON.stringify(Object.entries(localStorage)"
                ".filter(([k])=>k.includes('auth0')))",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = r.stdout.strip()
        if raw and "access_token" in raw:
            for _, v in json.loads(raw):
                try:
                    tok = json.loads(v).get("body", {}).get("access_token")
                    if tok:
                        return tok
                except Exception:
                    pass

        # Cookie fallback
        r = subprocess.run(
            [cli, "cookies", "get", "--url", "https://chat.openai.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for c in json.loads(r.stdout or "[]"):
            if "session-token" in c.get("name", ""):
                return c["value"]
    except Exception:
        pass
    return None


def _token_via_manual() -> str | None:
    """Open browser + ask user to paste token."""
    print()
    print("  Please log in to ChatGPT, then follow ONE of these steps:")
    print()
    print("  Option A — copy from browser console (easiest):")
    print("    1. Press F12 to open DevTools → Console tab")
    print("    2. Paste and run this:")
    print()
    print("       copy((Object.entries(localStorage).find(([k])=>")
    print(
        '         k.includes(\'auth0\'))||[])[1]?.match(/"access_token":"([^"]+)"/) ?.[1])'
    )
    print()
    print("    3. Paste the result below")
    print()
    print("  Option B — Codex CLI users:")
    print("    Run: cat ~/.codex/auth.json | python3 -c")
    print("         \"import json,sys; print(json.load(sys.stdin)['accessToken'])\"")
    print()
    webbrowser.open("https://chat.openai.com")
    token = input("  Paste token here: ").strip()
    return token or None


def get_token() -> str:
    h1("Step 1 — Log in to ChatGPT")

    # Silent sources first
    if t := _token_from_saved():
        ok("Using saved token")
        return t
    if t := _token_from_codex():
        ok("Found Codex CLI token")
        return t

    # Automated browser
    info("Opening chat.openai.com — log in if prompted...")
    if t := _token_via_browser_use():
        ok("Token extracted automatically")
        return t

    # Manual fallback
    if t := _token_via_manual():
        ok("Token received")
        return t

    raise SystemExit("Login cancelled. Re-run: openai-mcp setup")


def save_token(token: str) -> None:
    d = Path.home() / ".openai-mcp"
    d.mkdir(exist_ok=True)
    (d / "token.json").write_text(json.dumps({"access_token": token}))


# ── chatgpt2api ─────────────────────────────────────────────────────────────

CHAT2API_DIR = Path.home() / ".openai-mcp" / "chatgpt2api"
CHAT2API_REPO = "https://github.com/lanqian528/chat2api.git"


def _port_open(port: int) -> bool:
    import socket

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def ensure_chatgpt2api(token: str) -> str:
    """Ensure chatgpt2api is installed, configured, and running. Returns base_url."""
    h1("Step 2 — Start ChatGPT gateway")

    # Already running?
    if _port_open(3001):
        ok("ChatGPT gateway already running on :3001")
        return "http://localhost:3001/v1"

    # Install if needed
    if not CHAT2API_DIR.exists():
        info("Installing chatgpt2api (first time only)...")
        subprocess.run(
            ["git", "clone", "--depth=1", CHAT2API_REPO, str(CHAT2API_DIR)],
            check=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                str(CHAT2API_DIR / "requirements.txt"),
            ],
            check=True,
        )
        ok("chatgpt2api installed")
    else:
        ok("chatgpt2api found")

    # Write config
    cfg = {
        "auth-key": "openai-mcp-local",
        "refresh_account_interval_minute": 60,
        "proxy": "",
        "base_url": "http://localhost:3001",
    }
    (CHAT2API_DIR / "config.json").write_text(json.dumps(cfg, indent=2))

    # Import token
    _import_token(token)

    # Launch (background)
    info("Starting gateway...")
    log = open(Path.home() / ".openai-mcp" / "chatgpt2api.log", "w")
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "3001",
        ],
        cwd=CHAT2API_DIR,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )

    # Wait for it
    for _ in range(20):
        if _port_open(3001):
            ok("Gateway started on :3001")
            return "http://localhost:3001/v1"
        time.sleep(1)

    raise SystemExit("Gateway failed to start. Check ~/.openai-mcp/chatgpt2api.log")


def _import_token(token: str) -> None:
    """Write token into chatgpt2api's accounts file."""
    accounts_dir = CHAT2API_DIR / "accounts"
    accounts_dir.mkdir(exist_ok=True)
    account = {
        "email": "chatgpt-pro-user",
        "access_token": token,
    }
    (accounts_dir / "accounts.json").write_text(json.dumps([account]))


# ── detect plan ─────────────────────────────────────────────────────────────


def detect_plan(base_url: str, api_key: str) -> str:
    """Return 'pro', 'plus', or 'free'."""
    try:
        import urllib.request

        req = urllib.request.Request(
            base_url.rstrip("/") + "/../v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        models = [m["id"] for m in data.get("data", [])]
        if any("pro" in m or "o3-pro" in m or "research" in m for m in models):
            return "pro"
        if any("gpt-4" in m or "gpt-5" in m for m in models):
            return "plus"
    except Exception:
        pass
    return "plus"  # assume plus if can't detect


# ── MCP server ───────────────────────────────────────────────────────────────

MCP_CONFIG_PATH = Path.home() / ".openai-mcp" / "config.toml"
MCP_PORT = 9000


def write_mcp_config(base_url: str, api_key: str, plan: str) -> None:
    models_section = 'chat = "gpt-4o"\n'
    if plan in ("pro", "plus"):
        models_section += 'research = "research"\n'
    if plan == "pro":
        models_section += 'image = "gpt-image-2"\n'
        models_section = models_section.replace(
            'chat = "gpt-4o"', 'chat = "gpt-5-5-pro"'
        )

    cfg = f"""[api]
base_url = "{base_url}"
api_key  = "{api_key}"

[server]
host = "0.0.0.0"
port = {MCP_PORT}

[models]
{models_section}"""
    MCP_CONFIG_PATH.write_text(cfg)


def ensure_mcp_server() -> None:
    h1("Step 3 — Start MCP server")

    if _port_open(MCP_PORT):
        ok(f"MCP server already running on :{MCP_PORT}")
        return

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    with open(MCP_CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)

    log = open(Path.home() / ".openai-mcp" / "mcp.log", "w")
    subprocess.Popen(
        [sys.executable, "-m", "openai_mcp.server", "--config", str(MCP_CONFIG_PATH)],
        stdout=log,
        stderr=log,
        start_new_session=True,
    )

    for _ in range(15):
        if _port_open(MCP_PORT):
            ok(f"MCP server started on :{MCP_PORT}")
            return
        time.sleep(1)

    raise SystemExit("MCP server failed to start. Check ~/.openai-mcp/mcp.log")


def ensure_launchagent() -> None:
    """Install macOS LaunchAgent for persistence."""
    if platform.system() != "Darwin":
        return

    label = "com.user.openai-mcp"
    plist = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    binary = shutil.which("openai-mcp") or sys.executable

    cmd = (
        f"        <string>{binary}</string>\n"
        f"        <string>--config</string>\n"
        f"        <string>{MCP_CONFIG_PATH}</string>"
    )

    plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>Label</key><string>{label}</string>
    <key>ProgramArguments</key><array>
{cmd}
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>{Path.home()}/.openai-mcp/mcp.log</string>
    <key>StandardErrorPath</key><string>{Path.home()}/.openai-mcp/mcp.log</string>
</dict></plist>""")

    subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
    subprocess.run(["launchctl", "load", str(plist)], capture_output=True)


# ── agent CLI registration ───────────────────────────────────────────────────


def register_claude_code() -> bool:
    claude_json = Path.home() / ".claude.json"
    if not shutil.which("claude") and not claude_json.exists():
        return False

    try:
        data = json.loads(claude_json.read_text()) if claude_json.exists() else {}
    except Exception:
        data = {}

    data.setdefault("mcpServers", {})
    data["mcpServers"]["openai"] = {
        "type": "url",
        "url": f"http://localhost:{MCP_PORT}/mcp",
    }
    claude_json.write_text(json.dumps(data, indent=2))
    return True


def register_codex() -> bool:
    if not shutil.which("codex"):
        return False

    codex_cfg = Path.home() / ".codex" / "config.toml"
    note = (
        "# openai-mcp: standard models available via HTTP\n"
        '# base_url = "http://localhost:3001/v1"\n'
        "# Note: Pro models require the MCP tools in Claude Code\n"
    )
    if codex_cfg.exists():
        existing = codex_cfg.read_text()
        if "openai-mcp" not in existing:
            codex_cfg.write_text(note + existing)
    return True


def register_agents() -> None:
    h1("Step 4 — Register with agent CLIs")

    if register_claude_code():
        ok("Claude Code → ~/.claude.json updated")
        info("Restart Claude Code to activate tools")
    else:
        info("Claude Code not found (skipped)")

    if register_codex():
        ok("Codex CLI detected — note added to ~/.codex/config.toml")
    else:
        info("Codex CLI not found (skipped)")


# ── final summary ────────────────────────────────────────────────────────────


def print_summary(plan: str) -> None:
    tools = ["chat"]
    if plan in ("plus", "pro"):
        tools.append("research")
    if plan == "pro":
        tools.append("image_gen")

    print()
    print(f"{BOLD}{'─' * 50}{RESET}")
    print(f"{GREEN}{BOLD}  Done!{RESET}  ChatGPT {plan.capitalize()} is ready.")
    print(f"{'─' * 50}")
    print()
    print(f"  Plan:   ChatGPT {plan.capitalize()}")
    print(f"  Tools:  {', '.join(tools)}")
    print(f"  URL:    http://localhost:{MCP_PORT}/mcp")
    print()
    print("  In Claude Code (after restart), try:")
    if "research" in tools:
        print('    "Use deep_research to find the latest AI papers from 2025"')
    print('    "Use chat to ask gpt-5-5-pro to review this code"')
    print()
    print("  Logs:   ~/.openai-mcp/")
    print()


# ── entry point ──────────────────────────────────────────────────────────────


def run_setup() -> None:
    print(f"\n{BOLD}openai-mcp setup{RESET}")
    print("Use your ChatGPT Plus/Pro in Claude Code and other AI tools.\n")

    try:
        token = get_token()
        save_token(token)
        api_key = "openai-mcp-local"

        base_url = ensure_chatgpt2api(token)

        h1("Detecting plan...")
        plan = detect_plan(base_url, api_key)
        ok(f"ChatGPT {plan.capitalize()} detected")

        write_mcp_config(base_url, api_key, plan)
        ensure_mcp_server()
        if platform.system() == "Darwin":
            ensure_launchagent()
            ok("Auto-start enabled (LaunchAgent)")

        register_agents()
        print_summary(plan)

    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
