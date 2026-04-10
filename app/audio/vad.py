from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - optional runtime dependency
    ort = None


@dataclass(slots=True)
class FrameSpeechScore:
    probability: float
    backend: str


class SileroVAD:
    def __init__(self, model_path: str, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self._session = None
        self._input_names: list[str] = []
        self._output_name = ""
        path = Path(model_path)
        if ort is not None and path.exists():
            self._session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
            self._input_names = [inp.name for inp in self._session.get_inputs()]
            self._output_name = self._session.get_outputs()[0].name

    def score(self, pcm: np.ndarray) -> FrameSpeechScore:
        frame = np.asarray(pcm, dtype=np.float32).reshape(1, -1)
        if self._session is not None:
            try:
                out = self._run_onnx(frame)
                return FrameSpeechScore(probability=float(out), backend="silero-onnx")
            except Exception:
                pass
        return FrameSpeechScore(probability=_energy_probability(frame), backend="energy-fallback")

    def _run_onnx(self, frame: np.ndarray) -> float:
        assert self._session is not None
        feed: dict[str, np.ndarray | np.int64] = {}
        for name in self._input_names:
            lower = name.lower()
            if "sr" in lower or "sample_rate" in lower:
                feed[name] = np.array(self.sample_rate, dtype=np.int64)
            elif "state" in lower:
                feed[name] = np.zeros((2, 1, 128), dtype=np.float32)
            else:
                feed[name] = frame
        raw = self._session.run([self._output_name], feed)[0]
        arr = np.asarray(raw, dtype=np.float32).reshape(-1)
        return float(np.clip(arr[0] if arr.size else 0.0, 0.0, 1.0))


def _energy_probability(frame: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.square(frame)) + 1e-8))
    return float(np.clip((rms - 0.01) / 0.09, 0.0, 1.0))
