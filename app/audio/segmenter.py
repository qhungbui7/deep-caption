from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from app.config import VADConfig
from app.events import VAD
from app.models import AudioFrame, SpeechChunk

from .vad import SileroVAD


@dataclass(slots=True)
class _BufferedFrame:
    pcm: np.ndarray
    t0_ms: int
    t1_ms: int


class SpeechSegmenter(VAD):
    def __init__(
        self,
        config: VADConfig,
        sample_rate: int,
        partial_interval_ms: int = 400,
        max_chunk_ms: int = 6000,
    ) -> None:
        self.config = config
        self.sample_rate = sample_rate
        self.partial_interval_ms = max(100, partial_interval_ms)
        self.max_chunk_ms = max(1000, max_chunk_ms)
        self.vad = SileroVAD(config.model_path, sample_rate=sample_rate)

        self._frame_ms = 30
        self._preroll = deque(maxlen=max(1, config.preroll_ms // self._frame_ms))
        self._active_frames: list[_BufferedFrame] = []
        self._speech_ms = 0
        self._silence_ms = 0
        self._speaking = False
        self._last_partial_emit_ms = 0

    def feed(self, frame: AudioFrame) -> list[SpeechChunk]:
        score = self.vad.score(frame.pcm).probability
        buf = _BufferedFrame(frame.pcm, frame.t0_ms, frame.t1_ms)
        chunks: list[SpeechChunk] = []

        if not self._speaking:
            self._preroll.append(buf)
            if score >= self.config.start_threshold:
                self._speech_ms += self._frame_ms
                if self._speech_ms >= self.config.min_speech_ms:
                    self._speaking = True
                    self._active_frames.extend(self._preroll)
                    self._preroll.clear()
                    self._speech_ms = 0
                    self._last_partial_emit_ms = frame.t0_ms
            else:
                self._speech_ms = 0
            return chunks

        self._active_frames.append(buf)
        if score < self.config.end_threshold:
            self._silence_ms += self._frame_ms
        else:
            self._silence_ms = 0

        duration_ms = self._active_frames[-1].t1_ms - self._active_frames[0].t0_ms
        if duration_ms >= self.max_chunk_ms:
            chunks.append(self._finalize_chunk())
            self._active_frames.clear()
            self._speaking = False
            self._silence_ms = 0
            self._speech_ms = 0
            return chunks

        if frame.t1_ms - self._last_partial_emit_ms >= self.partial_interval_ms:
            partial = self._partial_chunk()
            if partial is not None:
                chunks.append(partial)
                self._last_partial_emit_ms = frame.t1_ms

        if self._silence_ms >= self.config.min_silence_ms:
            chunks.append(self._finalize_chunk())
            self._silence_ms = 0
            self._speaking = False
        return chunks

    def _finalize_chunk(self) -> SpeechChunk:
        if not self._active_frames:
            empty = np.zeros((0,), dtype=np.float32)
            return SpeechChunk(empty, self.sample_rate, 0, 0, True)
        pcm = np.concatenate([f.pcm for f in self._active_frames], axis=0).astype(np.float32)
        t0 = self._active_frames[0].t0_ms
        t1 = self._active_frames[-1].t1_ms
        self._active_frames.clear()
        return SpeechChunk(pcm=pcm, sample_rate=self.sample_rate, t0_ms=t0, t1_ms=t1, is_final=True)

    def _partial_chunk(self) -> SpeechChunk | None:
        if not self._active_frames:
            return None
        t1 = self._active_frames[-1].t1_ms
        t0_min = t1 - self.max_chunk_ms
        frames = [f for f in self._active_frames if f.t1_ms >= t0_min]
        if not frames:
            return None
        pcm = np.concatenate([f.pcm for f in frames], axis=0).astype(np.float32)
        return SpeechChunk(
            pcm=pcm,
            sample_rate=self.sample_rate,
            t0_ms=frames[0].t0_ms,
            t1_ms=frames[-1].t1_ms,
            is_final=False,
        )
