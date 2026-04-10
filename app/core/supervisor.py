from dataclasses import dataclass

from app.config import Config
from app.core.voice_runtime import VoiceRuntimeController
from app.models import TranslationSegment

@dataclass(slots=True)
class Supervisor:
    """Coordinates multi-process voice runtime."""

    config: Config
    source_id: str = ""
    target_lang: str = "vi"
    _runtime: VoiceRuntimeController | None = None

    def start(self) -> None:
        if self._runtime is not None:
            return
        self._runtime = VoiceRuntimeController(
            config=self.config,
            source_id=self.source_id,
            target_lang=self.target_lang,
        )
        self._runtime.start()

    def stop(self) -> None:
        if self._runtime is None:
            return
        self._runtime.stop()
        self._runtime = None

    def poll(self) -> list[TranslationSegment]:
        if self._runtime is None:
            return []
        return self._runtime.poll()
