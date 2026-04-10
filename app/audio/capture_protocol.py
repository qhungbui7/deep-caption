from __future__ import annotations

import json
import struct
from dataclasses import dataclass


@dataclass(slots=True)
class ControlMessage:
    kind: str
    payload: dict[str, object]

    def to_bytes(self) -> bytes:
        body = json.dumps({"kind": self.kind, "payload": self.payload}).encode("utf-8")
        return struct.pack(">I", len(body)) + body

    @classmethod
    def from_bytes(cls, data: bytes) -> "ControlMessage":
        raw = json.loads(data.decode("utf-8"))
        return cls(kind=str(raw["kind"]), payload=dict(raw.get("payload", {})))
