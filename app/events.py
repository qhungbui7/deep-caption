from abc import ABC, abstractmethod

from app.models import AudioFrame, SpeechChunk, TranscriptSegment


class AudioCapture(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> AudioFrame:
        raise NotImplementedError


class VAD(ABC):
    @abstractmethod
    def feed(self, frame: AudioFrame) -> list[SpeechChunk]:
        raise NotImplementedError


class ASREngine(ABC):
    @abstractmethod
    def transcribe(self, chunk: SpeechChunk, prompt: str) -> TranscriptSegment:
        raise NotImplementedError


class Overlay(ABC):
    @abstractmethod
    def show_partial(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def show_final(self, text: str, ttl_ms: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError
