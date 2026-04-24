"""openai-mcp — MCP server for any OpenAI-compatible API."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # pip install tomli

from openai import AsyncOpenAI
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "api": {"base_url": "http://localhost:3001/v1", "api_key": "sk-placeholder"},
    "server": {"host": "0.0.0.0", "port": 9000},
    "models": {"chat": "gpt-4o"},
}

_CONFIG_SEARCH = [
    Path("config.toml"),
    Path.home() / ".openai-mcp.toml",
    Path.home() / ".config" / "openai-mcp" / "config.toml",
]


def load_config(path: Path | None = None) -> dict[str, Any]:
    candidates = [path] if path else _CONFIG_SEARCH
    for p in candidates:
        if p and p.exists():
            with open(p, "rb") as f:
                data = tomllib.load(f)
            # Merge with defaults so missing keys don't crash
            merged = DEFAULT_CONFIG.copy()
            for section, values in data.items():
                merged.setdefault(section, {}).update(values)
            return merged
    return DEFAULT_CONFIG.copy()


# ---------------------------------------------------------------------------
# Build MCP server from config
# ---------------------------------------------------------------------------


def build_server(cfg: dict[str, Any]) -> FastMCP:
    api_cfg = cfg["api"]
    srv_cfg = cfg["server"]
    models_cfg = cfg["models"]

    client = AsyncOpenAI(base_url=api_cfg["base_url"], api_key=api_cfg["api_key"])

    mcp = FastMCP(
        "openai-mcp",
        host=srv_cfg.get("host", "0.0.0.0"),
        port=int(srv_cfg.get("port", 9000)),
        log_level="WARNING",
    )

    # ---- chat (always registered) -----------------------------------------
    chat_model = models_cfg.get("chat", "gpt-4o")

    @mcp.tool()
    async def chat(prompt: str, model: str = chat_model) -> str:
        """Send a message to the configured chat model.

        Leave `model` empty to use the default from config.
        """
        resp = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
        )
        return resp.choices[0].message.content or ""

    # ---- research (optional) ----------------------------------------------
    if "research" in models_cfg:
        research_model = models_cfg["research"]

        @mcp.tool()
        async def research(query: str) -> str:
            """Web search + synthesis with citations.

            Performs deep research on the query and returns a detailed report.
            Takes 30–90 seconds. Best for: current events, literature review,
            market research, fact-checking.
            """
            resp = await client.chat.completions.create(
                model=research_model,
                messages=[{"role": "user", "content": query}],
                max_tokens=4000,
            )
            return resp.choices[0].message.content or ""

    # ---- image_gen (optional) ---------------------------------------------
    if "image" in models_cfg:
        image_model = models_cfg["image"]

        @mcp.tool()
        async def image_gen(prompt: str) -> str:
            """Generate an image from a text description.

            Returns a base64-encoded PNG (data:image/png;base64,...).
            Takes 60–120 seconds. Describe the image in detail for best results.
            """
            resp = await client.images.generate(
                model=image_model,
                prompt=prompt,
                response_format="b64_json",
                size="1024x1024",
            )
            b64 = resp.data[0].b64_json
            return f"data:image/png;base64,{b64}"

    return mcp


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="openai-mcp",
        description="MCP server for any OpenAI-compatible API",
    )
    parser.add_argument("--config", type=Path, help="Path to config.toml")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio transport (for Claude Code legacy config)",
    )
    parser.add_argument("--port", type=int, help="Override server port")
    parser.add_argument("--host", help="Override server host")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.port:
        cfg["server"]["port"] = args.port
    if args.host:
        cfg["server"]["host"] = args.host

    mcp = build_server(cfg)
    tools = [k for k in cfg["models"]]

    if args.stdio:
        mcp.run(transport="stdio")
    else:
        host = cfg["server"]["host"]
        port = cfg["server"]["port"]
        print(
            f"openai-mcp → http://{host}:{port}/mcp  (tools: {', '.join(tools)})",
            flush=True,
        )
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
