import numpy as np


def resample_mono_float32(
    pcm: np.ndarray,
    src_rate: int,
    dst_rate: int = 16000,
) -> np.ndarray:
    mono = np.asarray(pcm, dtype=np.float32).reshape(-1)
    if src_rate == dst_rate or mono.size == 0:
        return mono
    src_x = np.linspace(0.0, 1.0, num=mono.size, endpoint=False)
    dst_size = max(1, int(mono.size * dst_rate / src_rate))
    dst_x = np.linspace(0.0, 1.0, num=dst_size, endpoint=False)
    return np.interp(dst_x, src_x, mono).astype(np.float32)
