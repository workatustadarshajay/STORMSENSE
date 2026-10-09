"""StormSense MCP client agent: a model that answers questions by calling the StormSense MCP tools.

It connects to the MCP server like any client would, discovers the tools, and lets a chat model
served by the Databricks workspace choose which to call. The model is reached with the workspace
login (the same CLI profile as the rest of the project), so no separate model API key is needed.

Read-only by default. Approve and reject are only offered when ALLOW_WRITES=1.

Run (with the MCP server on port 8200):
    uv run python mcp_agent.py "Which stores are at risk today?"
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from databricks.sdk import WorkspaceClient
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = os.environ.get("STORMSENSE_MCP_URL", "http://localhost:8200/mcp")
MODEL = os.environ.get("STORMSENSE_MCP_MODEL", "databricks-gemini-3-5-flash")
PROFILE = os.environ.get("DATABRICKS_PROFILE", "stormsense")
ALLOW_WRITES = os.environ.get("ALLOW_WRITES") == "1"
WRITE_TOOLS = {"stormsense_approve_transfers", "stormsense_reject_transfers"}
MAX_STEPS = 6

SYSTEM = (
    "You are a StormSense assistant for store planners. Use the tools to check live data before you answer. "
    "Make at most three checks, then answer in two or three plain sentences with no markdown. "
    "Name only transfer ids a tool returned."
)


def _text(content: Any) -> str:
    """Model replies come back as a string or as a list of content blocks, depending on the model."""
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict)).strip()
    return (content or "").strip()


def _tool_spec(tool: Any) -> dict[str, Any]:
    """Convert an MCP tool into the function-calling format the model expects."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": (tool.description or "").strip(),
            "parameters": tool.inputSchema,
        },
    }


async def answer(question: str) -> str:
    workspace = WorkspaceClient(profile=PROFILE)

    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [t for t in (await session.list_tools()).tools if ALLOW_WRITES or t.name not in WRITE_TOOLS]
            specs = [_tool_spec(t) for t in tools]

            messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": question},
            ]
            for step in range(MAX_STEPS):
                # On the last step no tools are offered, so the model has to write its answer.
                body = {"messages": messages, "tools": specs if step < MAX_STEPS - 1 else [], "max_tokens": 1500}
                reply = workspace.api_client.do("POST", f"/serving-endpoints/{MODEL}/invocations", body=body)
                message = reply["choices"][0]["message"]
                calls = message.get("tool_calls") or []
                if not calls:
                    return _text(message.get("content"))

                messages.append(message)
                for call in calls:
                    name = call["function"]["name"]
                    args = json.loads(call["function"].get("arguments") or "{}")
                    print(f"[check] {name} {args}", file=sys.stderr)
                    if name not in {t.name for t in tools}:
                        text = json.dumps({"ok": False, "error": "That tool is not available to this client."})
                    else:
                        result = await session.call_tool(name, args)
                        text = result.content[0].text if result.content else "{}"
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": text})
            return "I couldn't finish within the step limit. Try a narrower question."


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or "Which stores are at risk today, and what should planners do first?"
    print(asyncio.run(answer(question)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
