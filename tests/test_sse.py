"""Live SSE roundtrip: ask model to reply with PONG, verify stream parses."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest


@pytest.mark.skipif(
    not (Path.home() / ".codex" / "auth.json").exists(),
    reason="requires ~/.codex/auth.json",
)
@pytest.mark.skipif(
    os.environ.get("SKIP_LIVE") == "1",
    reason="SKIP_LIVE=1",
)
def test_sse_pong():
    from openai_mcp.backend import BackendClient
    from openai_mcp.sse import ConversationClient

    conv = ConversationClient(BackendClient())
    out = asyncio.run(
        conv.complete(
            "gpt-5-3",
            [{"role": "user", "content": "Reply with exactly: PONG"}],
        )
    )
    assert "pong" in out.lower(), f"no PONG in response: {out!r}"
