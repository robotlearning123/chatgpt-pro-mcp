# openai-mcp

A lightweight MCP server that connects **any OpenAI-compatible API** to Claude Code (and other MCP clients) in minutes.

Works with: OpenAI, chatgpt2api, LM Studio, Ollama, Together.ai, Groq, or any custom endpoint.

> **Personal use only.** See [Disclaimer](#disclaimer).

---

## Install

```bash
pip install git+https://github.com/robotlearning123/chatgpt-pro-mcp.git
```

Or clone and install locally:

```bash
git clone https://github.com/robotlearning123/chatgpt-pro-mcp
cd chatgpt-pro-mcp
pip install -e .
```

---

## Setup

**1. Create a config file**

```bash
cp config.example.toml config.toml   # or ~/.openai-mcp.toml
```

Edit it:

```toml
[api]
base_url = "http://localhost:3001/v1"
api_key  = "your-api-key"

[server]
host = "0.0.0.0"
port = 9000

[models]
chat     = "gpt-4o"       # required — default chat model
research = "research"     # optional — enables research tool
image    = "gpt-image-2"  # optional — enables image_gen tool
```

Config is searched in order: `./config.toml` → `~/.openai-mcp.toml` → `~/.config/openai-mcp/config.toml`

**2. Start the server**

```bash
openai-mcp
# → openai-mcp running at http://0.0.0.0:9000/mcp  (tools: chat, research, image)
```

**3. Add to Claude Code**

In `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "openai": {
      "type": "url",
      "url": "http://localhost:9000/mcp"
    }
  }
}
```

Restart Claude Code. Done.

---

## Tools

Tools are registered based on what's in `[models]`:

| Tool | Config key | Description |
|------|-----------|-------------|
| `chat` | `models.chat` | Chat with any model. Always enabled. |
| `research` | `models.research` | Deep web search + synthesis with citations. |
| `image_gen` | `models.image` | Generate an image, returns base64 PNG. |

Remove a key from `[models]` to disable that tool.

---

## Options

```
openai-mcp [--config PATH] [--host HOST] [--port PORT] [--stdio]

  --config PATH   Path to config.toml (overrides auto-search)
  --host HOST     Override bind host
  --port PORT     Override bind port
  --stdio         Use stdio transport instead of HTTP
```

---

## macOS: auto-start at login

```bash
bash install.sh
```

Installs a LaunchAgent so the server starts automatically and restarts if it crashes.

---

## stdio mode (Claude Code legacy)

If you prefer not to run a persistent server:

```json
{
  "mcpServers": {
    "openai": {
      "type": "stdio",
      "command": "openai-mcp",
      "args": ["--stdio", "--config", "/path/to/config.toml"]
    }
  }
}
```

---

## Common setups

<details>
<summary>ChatGPT Pro via chatgpt2api</summary>

```toml
[api]
base_url = "http://localhost:3001/v1"
api_key  = "your-chatgpt2api-key"

[models]
chat     = "gpt-5-5-pro"
research = "research"
image    = "gpt-image-2"
```

→ [chatgpt2api](https://github.com/lanqian528/chat2api)
</details>

<details>
<summary>OpenAI API</summary>

```toml
[api]
base_url = "https://api.openai.com/v1"
api_key  = "sk-..."

[models]
chat  = "gpt-4o"
image = "dall-e-3"
```
</details>

<details>
<summary>Local model via Ollama</summary>

```toml
[api]
base_url = "http://localhost:11434/v1"
api_key  = "ollama"

[models]
chat = "llama3.2"
```
</details>

<details>
<summary>Groq (fast inference)</summary>

```toml
[api]
base_url = "https://api.groq.com/openai/v1"
api_key  = "gsk_..."

[models]
chat = "llama-3.3-70b-versatile"
```
</details>

---

## Disclaimer

**This project is for personal, non-commercial use only.**

- This is a local bridge between MCP clients and an OpenAI-compatible API. It does not bypass, crack, or redistribute any proprietary API.
- You are responsible for complying with the terms of service of whichever API you connect to.
- Do not use this to resell API access, serve third parties, or build commercial products.
- Do not expose the server to the public internet without authentication.
- This project is not affiliated with OpenAI or Anthropic.

## License

[MIT](LICENSE) — personal use only. Commercial use is not permitted.
