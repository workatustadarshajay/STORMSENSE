#!/usr/bin/env python3
"""StormSense MCP demo client: talks to the StormSense MCP server like any outside app would.

No MCP SDK needed. It speaks JSON-RPC 2.0 over the Streamable HTTP endpoint directly,
the same wire protocol an AI assistant uses.

Steps:
  1. initialize and initialized handshake      (MCP lifecycle)
  2. tools/list                                (what can a client do?)
  3. stormsense_overview                       (what needs attention today?)
  4. stormsense_list_transfers                 (urgent moves waiting for a decision)
  5. stormsense_what_if                        (cost of a storm, read-only)
  6. stormsense_storm_desk_plan (optional)     (the crew's plan, about a minute)
  7. stormsense_approve_transfers (optional)   (writes: approves one urgent move)

Usage:
    uv run python demo_client.py                    # read-only steps 1-5
    uv run python demo_client.py --agent            # also step 6
    uv run python demo_client.py --approve          # also step 7 (changes data)
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request

ACCEPT = "application/json, text/event-stream"
TIMEOUT = 150


class McpClient:
    """Minimal MCP client over Streamable HTTP (JSON-RPC 2.0)."""

    def __init__(self, base: str):
        self.endpoint = base.rstrip("/") + "/mcp"
        self.session_id: str | None = None
        self._next_id = 0

    def _post(self, payload: dict) -> dict | None:
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Accept": ACCEPT},
            method="POST",
        )
        if self.session_id:
            req.add_header("mcp-session-id", self.session_id)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            self.session_id = resp.headers.get("mcp-session-id") or self.session_id
            body = resp.read().decode()
        if not body.strip():
            return None
        if "\ndata:" in body or body.startswith(("data:", "event:")):
            # Streamable HTTP may answer as Server-Sent Events; the last data line holds the result.
            data_lines = [ln[5:].strip() for ln in body.splitlines() if ln.startswith("data:")]
            return json.loads(data_lines[-1]) if data_lines else None
        return json.loads(body)

    def request(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        payload: dict = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            payload["params"] = params
        resp = self._post(payload)
        if resp is None:
            raise RuntimeError(f"{method}: empty response")
        if "error" in resp:
            raise RuntimeError(f"{method}: JSON-RPC error {resp['error']}")
        return resp["result"]

    def notify(self, method: str) -> None:
        self._post({"jsonrpc": "2.0", "method": method})

    def initialize(self) -> dict:
        result = self.request(
            "initialize",
            {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "stormsense-demo-client", "version": "1.0"}},
        )
        self.notify("notifications/initialized")
        return result

    def tools_list(self) -> list[dict]:
        return self.request("tools/list")["tools"]

    def call(self, name: str, arguments: dict) -> dict | list:
        """Call a tool and return its JSON result."""
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        text = result["content"][0]["text"] if result.get("content") else "{}"
        return json.loads(text)


def hr(title: str) -> None:
    print(f"\n{'─' * 62}\n{title}\n{'─' * 62}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://localhost:8200", help="StormSense MCP server base URL")
    ap.add_argument("--agent", action="store_true", help="also ask the storm desk crew for a plan (about a minute)")
    ap.add_argument("--approve", action="store_true", help="also approve one urgent pending transfer (changes data)")
    args = ap.parse_args()

    client = McpClient(args.base)

    hr("1 · initialize")
    info = client.initialize()
    print(f"server   : {info['serverInfo']['name']}")
    print(f"protocol : {info['protocolVersion']}")

    hr("2 · tools/list")
    tools = client.tools_list()
    for t in tools:
        kind = "read " if t.get("annotations", {}).get("readOnlyHint") else "WRITE"
        print(f"  [{kind}] {t['name']}")

    hr("3 · stormsense_overview")
    overview = client.call("stormsense_overview", {})
    print(f"  urgent transfers   : {overview.get('urgent_transfers')}")
    print(f"  waiting for a call : {overview.get('pending_transfers')}")
    print(f"  stores at risk     : {overview.get('stores_at_risk')}")

    hr("4 · stormsense_list_transfers (urgent, waiting)")
    urgent = client.call("stormsense_list_transfers", {"status": "PENDING", "urgency": "URGENT"})
    if not isinstance(urgent, list):
        print(f"  {urgent.get('error', 'no transfers returned')}")
        return 1
    for t in urgent[:5]:
        print(f"  {t['id']}  {t['qty']:>4} x {t['product']['name']:<22} {t['from_store']['name']} -> {t['to_store']['name']}")
    if not urgent:
        print("  (no urgent transfers waiting)")

    hr("5 · stormsense_what_if (Florida, strength 80, two days, read-only)")
    what_if = client.call("stormsense_what_if", {"strength": 80, "start_day": 0, "days": 2, "region": "Florida"})
    print(json.dumps(what_if, indent=2, ensure_ascii=False)[:1200])

    if args.agent:
        hr("6 · stormsense_storm_desk_plan")
        plan = client.call("stormsense_storm_desk_plan", {"goal": "Prepare Florida for this weekend's storm"})
        print(plan.get("plan") or plan.get("message") or plan)

    if args.approve:
        hr("7 · stormsense_approve_transfers (one urgent move)")
        if urgent:
            result = client.call("stormsense_approve_transfers", {"ids": [urgent[0]["id"]], "note": "Approved through MCP demo"})
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("  nothing urgent to approve")

    hr("Demo complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
