"""AstrBot plugin runtime (OOP) scaffolding.

This package provides minimal building blocks for running plugins in a
subprocess with a JSON-RPC over stdio protocol. Not wired into the main
loading flow yet.
"""

__all__ = [
    "rpc_protocol",
    "worker_bootstrap",
    "process_manager",
]
