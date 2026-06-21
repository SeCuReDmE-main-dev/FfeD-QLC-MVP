from __future__ import annotations

import os
import socket


def emit_dogstatsd_counter(name: str, value: int = 1, tags: tuple[str, ...] = ()) -> None:
    host = os.environ.get("DD_DOGSTATSD_HOST", "127.0.0.1")
    port = int(os.environ.get("DD_DOGSTATSD_PORT", "8125"))
    tag_suffix = f"|#{','.join(tags)}" if tags else ""
    payload = f"{name}:{value}|c{tag_suffix}".encode("utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (host, port))

