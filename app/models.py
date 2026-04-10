from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class AudioFrame:
    pcm: np.ndarray
    sample_rate: int
    t0_ms: int
    t1_ms: int
    source_id: str


@dataclass(slots=True)
class SpeechChunk:
    pcm: np.ndarray
    sample_rate: int
    t0_ms: int
    t1_ms: int
    is_final: bool


@dataclass(slots=True)
class TranscriptSegment:
    text: str
    language: str
    t0_ms: int
    t1_ms: int
    is_final: bool


@dataclass(slots=True)
class TranslationSegment:
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    t0_ms: int
    t1_ms: int
    is_final: bool
