from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from queue import Queue, Empty
from typing import Any, Dict, Iterable

from .rpc_protocol import make_request, parse_json_line


def _reader_thread(stream, q: Queue) -> None:
    for line in iter(stream.readline, ""):
        q.put(line)
    stream.close()


class PluginProcess:
    def __init__(self, python_exec: str, worker_path: str, *, env: Dict[str, str]) -> None:
        self.python_exec = python_exec
        self.worker_path = worker_path
        self.env = env
        self.proc: subprocess.Popen[str] | None = None
        self._stdout_q: Queue[str] = Queue()
        self._reader: threading.Thread | None = None

    def start(self) -> None:
        if self.proc is not None:
            return
        self.proc = subprocess.Popen(
            [self.python_exec, self.worker_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env={**os.environ, **self.env},
        )
        assert self.proc.stdout is not None and self.proc.stdin is not None
        self._reader = threading.Thread(target=_reader_thread, args=(self.proc.stdout, self._stdout_q), daemon=True)
        self._reader.start()

    def send(self, obj: Dict[str, Any]) -> None:
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("process not started")
        data = json.dumps(obj, ensure_ascii=False) + "\n"
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def recv(self, timeout: float | None = None) -> Dict[str, Any] | None:
        try:
            line = self._stdout_q.get(timeout=timeout)
        except Empty:
            return None
        return parse_json_line(line)

    def stop(self) -> None:
        if not self.proc:
            return
        try:
            self.send(make_request("shutdown", id=0))
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
        self.proc = None
