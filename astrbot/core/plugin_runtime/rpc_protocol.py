from __future__ import annotations

import dataclasses
import json
import sys
from typing import Any, Dict, Iterable, Optional


JSONDict = Dict[str, Any]


@dataclasses.dataclass(frozen=True)
class JSONRPCError:
    code: int
    message: str
    data: Any | None = None

    def to_dict(self) -> JSONDict:
        payload: JSONDict = {"code": self.code, "message": self.message}
        if self.data is not None:
            payload["data"] = self.data
        return payload


def make_request(method: str, *, params: Any = None, id: Any | None = None) -> JSONDict:
    req: JSONDict = {"jsonrpc": "2.0", "method": method}
    if id is not None:
        req["id"] = id
    if params is not None:
        req["params"] = params
    return req


def make_response(result: Any, *, id: Any) -> JSONDict:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def make_error(error: JSONRPCError, *, id: Any | None) -> JSONDict:
    resp: JSONDict = {"jsonrpc": "2.0", "error": error.to_dict()}
    if id is not None:
        resp["id"] = id
    return resp


def write_json_lines(messages: Iterable[JSONDict], stream = sys.stdout) -> None:
    for msg in messages:
        stream.write(json.dumps(msg, ensure_ascii=False) + "\n")
        stream.flush()


def parse_json_line(line: str) -> JSONDict | None:
    line = line.strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
        if isinstance(obj, dict) and obj.get("jsonrpc") == "2.0":
            return obj
    except Exception:
        return None
    return None
