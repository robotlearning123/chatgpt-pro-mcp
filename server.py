#!/usr/bin/env python3
"""
ChatGPT Pro MCP Server
Exposes ChatGPT Pro models as MCP tools for Claude Code and other MCP clients.

Transport modes:
  HTTP (default): python3 server.py          → http://0.0.0.0:9000/mcp
  stdio:          python3 server.py --stdio   → pipe (Claude Code legacy)

Config via environment variables:
  CHATGPT_BASE_URL  OpenAI-compatible base URL  (default: http://localhost:3001/v1)
  CHATGPT_API_KEY   API key                      (default: sk-placeholder)
  MCP_HOST          Bind host                    (default: 0.0.0.0)
  MCP_PORT          Bind port                    (default: 9000)
"""

import os
import sys

from openai import AsyncOpenAI
from mcp.server.fastmcp import FastMCP

BASE_URL = os.environ.get("CHATGPT_BASE_URL", "http://localhost:3001/v1")
API_KEY = os.environ.get("CHATGPT_API_KEY", "sk-placeholder")
HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_PORT", "9000"))

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)

mcp = FastMCP("chatgpt-pro", host=HOST, port=PORT, log_level="WARNING")


@mcp.tool()
async def ask_gpt_pro(prompt: str, model: str = "gpt-5-5-pro") -> str:
    """Ask a ChatGPT Pro model.

    Available models: gpt-5-5-pro, gpt-5-4-pro, o3-pro, gpt-5-5-thinking, research
    Best for: complex reasoning, long-context tasks, architecture decisions.
    """
    resp = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
    )
    return resp.choices[0].message.content or ""


@mcp.tool()
async def deep_research(query: str) -> str:
    """ChatGPT Deep Research — web search + synthesis with citations.

    Best for: current events, literature review, market research, fact-checking.
    Returns a detailed report. Takes 30–90 seconds.
    """
    resp = await client.chat.completions.create(
        model="research",
        messages=[{"role": "user", "content": query}],
        max_tokens=4000,
    )
    return resp.choices[0].message.content or ""


@mcp.tool()
async def gpt_image_gen(prompt: str) -> str:
    """Generate an image with gpt-image-2 (ChatGPT Pro).

    Returns a base64-encoded PNG (~100 KB). Takes 60–120 seconds.
    Describe the image in detail for best results.
    """
    resp = await client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        response_format="b64_json",
        size="1024x1024",
    )
    b64 = resp.data[0].b64_json
    return f"data:image/png;base64,{b64}"


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run(transport="stdio")
    else:
        print(f"ChatGPT Pro MCP server → http://{HOST}:{PORT}/mcp", flush=True)
        mcp.run(transport="streamable-http")
