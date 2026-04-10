from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

from app.config import ASRConfig
from app.events import ASREngine
from app.models import SpeechChunk, TranscriptSegment

from .postprocess import normalize_transcript


class WhisperCppASR(ASREngine):
    def __init__(self, config: ASRConfig) -> None:
        self.config = config
        self._binary = Path(config.binary_path)
        self._model = Path(config.model)

    def transcribe(self, chunk: SpeechChunk, prompt: str) -> TranscriptSegment:
        if chunk.pcm.size == 0:
            return TranscriptSegment("", "und", chunk.t0_ms, chunk.t1_ms, chunk.is_final)

        if not self._binary.exists() or not self._model.exists():
            return TranscriptSegment("", "und", chunk.t0_ms, chunk.t1_ms, chunk.is_final)

        with tempfile.TemporaryDirectory(prefix="deep-caption-") as temp_dir:
            wav_path = Path(temp_dir) / "chunk.wav"
            self._write_wav(wav_path, chunk.pcm, chunk.sample_rate)

            cmd = [
                str(self._binary),
                "--mode",
                "transcribe",
                "--model",
                str(self._model),
                "--audio",
                str(wav_path),
                "--language",
                self.config.language,
                "--prompt",
                prompt,
                "--threads",
                str(self.config.threads),
                "--json",
            ]
            completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
            payload = self._parse_json(completed.stdout)
            text = normalize_transcript(payload.get("text", ""))
            language = payload.get("language", "und")
            return TranscriptSegment(
                text=text,
                language=language,
                t0_ms=int(payload.get("start_ms", chunk.t0_ms)),
                t1_ms=int(payload.get("end_ms", chunk.t1_ms)),
                is_final=chunk.is_final,
            )

    @staticmethod
    def _write_wav(path: Path, pcm: np.ndarray, sample_rate: int) -> None:
        clipped = np.clip(pcm, -1.0, 1.0)
        pcm16 = (clipped * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm16.tobytes())

    @staticmethod
    def _parse_json(raw: str) -> dict[str, object]:
        text = raw.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            lines = [line for line in text.splitlines() if line.strip().startswith("{")]
            if not lines:
                return {}
            try:
                return json.loads(lines[-1])
            except json.JSONDecodeError:
                return {}
