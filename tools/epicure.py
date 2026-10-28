#!/usr/bin/env python
"""Minimal Epicure MCP client (Streamable HTTP).

Why this exists: the Epicure MCP tools are registered in Hermes but only load in a NEW session.
This is the interim path for the current one — and the reusable helper for any later script.

    python tools/epicure.py targets
    python tools/epicure.py neighbors tomato
    python tools/epicure.py pairing tomato basil
    python tools/epicure.py compare miso "soy sauce" --axis savoury
    python tools/epicure.py call <tool_name> '<json-args>'

PITFALL (measured 2026-10-25): the server returns **403 Forbidden** when the User-Agent is
`Python-urllib/*`. It is a UA filter, not auth — there is no auth. Always send a real UA.
Host/origin allowlists are also enforced, so no Origin header is sent.
"""
from __future__ import annotations

import json
import sys
import urllib.request

URL = "https://epicure-mcp.kaikaku.ai/mcp"
UA = "HermesAgent/1.0 (Larder research)"


class Epicure:
    def __init__(self, url: str = URL) -> None:
        self.url = url
        self.sid: str | None = None
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "HermesAgent", "version": "1.0"},
        })

    def _rpc(self, method: str, params: dict | None = None) -> dict:
        body: dict = {"jsonrpc": "2.0", "id": 1, "method": method}
        if params is not None:
            body["params"] = params
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": UA,                      # <- the 403 fix
        }
        if self.sid:
            headers["Mcp-Session-Id"] = self.sid
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=headers,
                                     method="POST")
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode()
            self.sid = r.headers.get("Mcp-Session-Id") or self.sid
        data = [ln[6:] for ln in raw.splitlines() if ln.startswith("data: ")]
        if not data:
            raise RuntimeError(f"no SSE payload for {method}: {raw[:300]!r}")
        out = json.loads(data[-1])
        if "error" in out:
            raise RuntimeError(f"{method} -> {out['error']}")
        return out["result"]

    def call(self, tool: str, **args) -> object:
        res = self._rpc("tools/call", {"name": tool, "arguments": args})
        text = "".join(c.get("text", "") for c in res.get("content", []))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    e = Epicure()
    cmd, rest = argv[1], argv[2:]
    if cmd == "targets":
        out = e.call("list_targets")
    elif cmd == "neighbors":
        out = e.call("neighbors", ingredient=rest[0])
    elif cmd == "pairing":
        out = e.call("pairing_score", ingredient_a=rest[0], ingredient_b=rest[1])
    elif cmd == "compare":
        axis = None
        if "--axis" in rest:
            i = rest.index("--axis")
            axis = rest[i + 1]
            rest = rest[:i]
        kw = {"ingredient_a": rest[0], "ingredient_b": rest[1]}
        if axis:
            kw["axis"] = axis
        out = e.call("compare_on_axis", **kw)
    elif cmd == "call":
        out = e.call(rest[0], **json.loads(rest[1] if len(rest) > 1 else "{}"))
    else:
        print(__doc__)
        return 2
    print(json.dumps(out, indent=2)[:12000] if not isinstance(out, str) else out[:12000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
