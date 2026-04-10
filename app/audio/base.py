from abc import ABC, abstractmethod

from app.models import AudioFrame


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
