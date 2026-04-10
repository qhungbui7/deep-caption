from dataclasses import dataclass
import json
import struct

import numpy as np

from app.models import AudioFrame


@dataclass(slots=True)
class BridgeControl:
    action: str
    source_id: str | None = None

    def to_bytes(self) -> bytes:
        payload = {"action": self.action, "source_id": self.source_id}
        raw = json.dumps(payload).encode("utf-8")
        return struct.pack(">I", len(raw)) + raw


def decode_framed_audio(payload: bytes) -> AudioFrame:
    header_len = struct.unpack(">I", payload[:4])[0]
    header_raw = payload[4 : 4 + header_len]
    header = json.loads(header_raw.decode("utf-8"))
    pcm_raw = payload[4 + header_len :]
    pcm = np.frombuffer(pcm_raw, dtype=np.float32).copy()
    return AudioFrame(
        pcm=pcm,
        sample_rate=int(header["sample_rate"]),
        t0_ms=int(header["t0_ms"]),
        t1_ms=int(header["t1_ms"]),
        source_id=str(header["source_id"]),
    )
