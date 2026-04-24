# chatgpt-pro-mcp

An MCP server that exposes **ChatGPT Pro models** to Claude Code and any other MCP client — one running process, shared by all agents.

## What it does

Wraps an OpenAI-compatible API (e.g. [chatgpt2api](https://github.com/lanqian528/chat2api)) and serves three tools over HTTP:

| Tool | Model | Use for |
|------|-------|---------|
| `ask_gpt_pro` | gpt-5-5-pro (default), gpt-5-4-pro, o3-pro, gpt-5-5-thinking | Reasoning, code, long-context |
| `deep_research` | research | Web search + synthesis with citations |
| `gpt_image_gen` | gpt-image-2 | Image generation (returns base64 PNG) |

## Requirements

- Python 3.10+
- A running OpenAI-compatible API pointed at your ChatGPT Pro account  
  → [chatgpt2api](https://github.com/lanqian528/chat2api) works well for this

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/chatgpt-pro-mcp
cd chatgpt-pro-mcp
pip install -r requirements.txt

# Run (HTTP mode, default port 9000)
CHATGPT_BASE_URL=http://localhost:3001/v1 \
CHATGPT_API_KEY=your-key \
python3 server.py
```

## macOS auto-start

```bash
bash install.sh   # interactive — prompts for URL, key, port
```

Installs a LaunchAgent that keeps the server alive across reboots.

## Connect to Claude Code

Add to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "chatgpt-pro": {
      "type": "url",
      "url": "http://localhost:9000/mcp"
    }
  }
}
```

Restart Claude Code. Tools appear as `mcp__chatgpt-pro__ask_gpt_pro`, etc.

## Connect from any HTTP client

The server speaks [MCP streamable-http](https://spec.modelcontextprotocol.io/specification/basic/transports/).  
Quick smoke-test:

```bash
curl http://localhost:9000/mcp \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `CHATGPT_BASE_URL` | `http://localhost:3001/v1` | OpenAI-compatible base URL |
| `CHATGPT_API_KEY` | `sk-placeholder` | API key |
| `MCP_HOST` | `0.0.0.0` | Bind host |
| `MCP_PORT` | `9000` | Bind port |

## stdio mode (legacy)

```bash
python3 server.py --stdio
```

```json
{
  "mcpServers": {
    "chatgpt-pro": {
      "type": "stdio",
      "command": "python3",
      "args": ["/path/to/server.py", "--stdio"],
      "env": {
        "CHATGPT_BASE_URL": "http://localhost:3001/v1",
        "CHATGPT_API_KEY": "your-key"
      }
    }
  }
}
```

## License

MIT
