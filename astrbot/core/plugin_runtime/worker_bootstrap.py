from __future__ import annotations

import os
import sys
import traceback
from typing import Any, Dict

from .rpc_protocol import (
    JSONRPCError,
    make_error,
    make_response,
    make_request,
    parse_json_line,
    write_json_lines,
)


def _notify_ready() -> None:
    msg = make_request("worker.ready", params={"pid": os.getpid()})
    write_json_lines([msg])


def _handle_request(obj: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    method = obj.get("method")
    _id = obj.get("id")
    params = obj.get("params") or {}

    try:
        if method == "initialize":
            # Expected params: { plugin_root, site_packages, config, env }
            state["initialized"] = True
            state["plugin_root"] = params.get("plugin_root")
            state["site_packages"] = params.get("site_packages")
            return make_response({"ok": True}, id=_id)

        if method == "list_capabilities":
            # Minimal placeholder; real implementation should introspect plugin
            result = {"metadata": {}, "handlers": [], "tools": []}
            return make_response(result, id=_id)

        if method == "handle_event":
            # Placeholder: accept and return empty processing result
            return make_response({"messages": [], "state_updates": {}}, id=_id)

        if method == "call_tool":
            # Placeholder: not implemented; return ok:false semantics in result
            return make_response({"ok": False, "reason": "not_implemented"}, id=_id)

        if method == "cancel":
            return make_response({"ok": True}, id=_id)

        if method == "shutdown":
            return make_response({"ok": True}, id=_id)

        return make_error(JSONRPCError(-32601, f"Method not found: {method}"), id=_id)
    except Exception as exc:
        return make_error(
            JSONRPCError(-32003, "worker unhandled error", data=traceback.format_exc()),
            id=_id,
        )


def _apply_pythonpath_from_env() -> None:
    # Allow launcher to provide additional search paths
    extra_paths = []
    root = os.environ.get("ASTRBOT_PLUGIN_ROOT")
    site = os.environ.get("ASTRBOT_PLUGIN_SITE_PACKAGES")
    if site:
        extra_paths.append(site)
    if root:
        extra_paths.append(root)
    for p in extra_paths:
        if p and os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def main() -> int:
    # Ensure stdout is unbuffered
    try:
        import msvcrt  # type: ignore
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)  # type: ignore[attr-defined]
    except Exception:
        pass

    _apply_pythonpath_from_env()
    _notify_ready()

    state: Dict[str, Any] = {"initialized": False}

    for raw in sys.stdin:
        obj = parse_json_line(raw)
        if not isinstance(obj, dict):
            continue
        resp = _handle_request(obj, state)
        write_json_lines([resp])

        # Stop loop when shutdown acknowledged
        try:
            if obj.get("method") == "shutdown":
                break
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
