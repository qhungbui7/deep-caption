from collections import deque

import numpy as np


class AudioRingBuffer:
    def __init__(self, sample_rate: int, max_seconds: int = 8) -> None:
        self.sample_rate = sample_rate
        self.max_samples = sample_rate * max_seconds
        self._frames: deque[np.ndarray] = deque()
        self._size = 0

    def push(self, pcm: np.ndarray) -> None:
        if pcm.size == 0:
            return
        chunk = np.asarray(pcm, dtype=np.float32).reshape(-1)
        self._frames.append(chunk)
        self._size += chunk.size
        while self._size > self.max_samples and self._frames:
            old = self._frames.popleft()
            self._size -= old.size

    def read_all(self) -> np.ndarray:
        if not self._frames:
            return np.zeros((0,), dtype=np.float32)
        return np.concatenate(list(self._frames), axis=0)
