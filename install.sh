#!/usr/bin/env bash
# ChatGPT Pro MCP Server — one-command installer
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_LABEL="com.user.chatgpt-pro-mcp"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

echo "=== ChatGPT Pro MCP Server Installer ==="

# 1. Check Python
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install from https://python.org"
  exit 1
fi

# 2. Install dependencies
echo "[1/3] Installing Python dependencies..."
pip3 install -q -r "$REPO_DIR/requirements.txt"

# 3. Prompt for config
echo ""
echo "[2/3] Configuration"
read -rp "  CHATGPT_BASE_URL [http://localhost:3001/v1]: " BASE_URL
BASE_URL="${BASE_URL:-http://localhost:3001/v1}"
read -rp "  CHATGPT_API_KEY: " API_KEY
read -rp "  MCP_PORT [9000]: " PORT
PORT="${PORT:-9000}"

# 4. Write LaunchAgent
echo ""
echo "[3/3] Installing LaunchAgent (auto-start at login)..."
cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(command -v python3)</string>
        <string>$REPO_DIR/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$REPO_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$REPO_DIR/server.log</string>
    <key>StandardErrorPath</key>
    <string>$REPO_DIR/server.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>CHATGPT_BASE_URL</key>
        <string>$BASE_URL</string>
        <key>CHATGPT_API_KEY</key>
        <string>$API_KEY</string>
        <key>MCP_PORT</key>
        <string>$PORT</string>
    </dict>
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
sleep 2

# 5. Verify
if curl -sf "http://localhost:$PORT/mcp" \
    -X POST -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"install-check","version":"1"}}}' \
    | grep -q "chatgpt-pro"; then
  echo ""
  echo "✓ Server running at http://localhost:$PORT/mcp"
else
  echo "WARNING: Server may not be running. Check: tail -f $REPO_DIR/server.log"
fi

echo ""
echo "=== Add to Claude Code (~/.claude.json mcpServers) ==="
echo '{'
echo "  \"chatgpt-pro\": { \"type\": \"url\", \"url\": \"http://localhost:$PORT/mcp\" }"
echo '}'
echo ""
echo "Done. Restart Claude Code to pick up the new MCP server."
