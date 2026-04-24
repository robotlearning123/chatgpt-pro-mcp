#!/usr/bin/env bash
# openai-mcp — macOS LaunchAgent installer
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_LABEL="com.user.openai-mcp"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

echo "=== openai-mcp installer ==="

# 1. Install package
echo "[1/3] Installing openai-mcp..."
pip3 install -q -e "$REPO_DIR"

BINARY="$(command -v openai-mcp)"
if [ -z "$BINARY" ]; then
  echo "ERROR: openai-mcp not found after install. Check your PATH."
  exit 1
fi

# 2. Config
CONFIG="$REPO_DIR/config.toml"
if [ ! -f "$CONFIG" ]; then
  echo ""
  echo "[2/3] No config.toml found. Creating from example..."
  cp "$REPO_DIR/config.example.toml" "$CONFIG"
  echo "      Edit $CONFIG before continuing."
  echo "      Then re-run: bash install.sh"
  exit 0
fi
echo "[2/3] Using config: $CONFIG"

# 3. LaunchAgent
echo "[3/3] Installing LaunchAgent..."
cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BINARY</string>
        <string>--config</string>
        <string>$CONFIG</string>
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
</dict>
</plist>
PLIST

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
sleep 2

# Detect port from config
PORT=$(python3 -c "
try:
    import tomllib
except ImportError:
    import tomli as tomllib
with open('$CONFIG', 'rb') as f:
    c = tomllib.load(f)
print(c.get('server', {}).get('port', 9000))
" 2>/dev/null || echo 9000)

# 4. Verify
if curl -sf "http://localhost:$PORT/mcp" \
    -X POST -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"install-check","version":"1"}}}' \
    | grep -q "openai-mcp"; then
  echo ""
  echo "✓ Server running at http://localhost:$PORT/mcp"
else
  echo "WARNING: Server may not have started. Check: tail -f $REPO_DIR/server.log"
fi

echo ""
echo "Add to ~/.claude.json:"
echo '{'
echo "  \"mcpServers\": {"
echo "    \"openai\": { \"type\": \"url\", \"url\": \"http://localhost:$PORT/mcp\" }"
echo "  }"
echo '}'
