from __future__ import annotations

import subprocess
import time

import numpy as np

from app.audio.base import AudioCapture
from app.models import AudioFrame


class PulseAudioCapture(AudioCapture):
    def __init__(self, sample_rate: int = 16000, frame_ms: int = 30, source_id: str = "") -> None:
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.source_id = source_id
        self._proc: subprocess.Popen[bytes] | None = None
        self._t_ms = 0

    def start(self) -> None:
        if self._proc is not None:
            return
        cmd = [
            "parec",
            "--format=float32le",
            f"--rate={self.sample_rate}",
            "--channels=1",
        ]
        device = _extract_pulse_device(self.source_id)
        if device:
            cmd.append(f"--device={device}")
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("parec is not available") from exc
        self._t_ms = int(time.monotonic() * 1000)

    def stop(self) -> None:
        if self._proc is None:
            return
        self._proc.terminate()
        self._proc.wait(timeout=2)
        self._proc = None

    def read(self) -> AudioFrame:
        if self._proc is None or self._proc.stdout is None:
            raise RuntimeError("PulseAudio capture is not started")
        samples = int(self.sample_rate * self.frame_ms / 1000)
        needed = samples * 4
        raw = self._proc.stdout.read(needed)
        if not raw or len(raw) < needed:
            raise RuntimeError("PulseAudio stream ended")
        pcm = np.frombuffer(raw, dtype=np.float32).copy()
        t0 = self._t_ms
        t1 = t0 + self.frame_ms
        self._t_ms = t1
        return AudioFrame(
            pcm=pcm,
            sample_rate=self.sample_rate,
            t0_ms=t0,
            t1_ms=t1,
            source_id=self.source_id or "pulseaudio",
        )


def _extract_pulse_device(source_id: str) -> str:
    if source_id.startswith("pulse:"):
        return source_id.split(":", 1)[1]
    if source_id.startswith("pulse-id:"):
        return source_id.split(":", 1)[1]
    return ""
