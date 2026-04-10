from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class AppConfig:
    mode: str = "text"
    target_language: str = "vi"
    show_source_text: bool = True
    overlay_enabled: bool = True


@dataclass(slots=True)
class TranslationConfig:
    backend: str = "auto"
    argos_enabled: bool = True
    opus_enabled: bool = True
    nllb_enabled: bool = False
    prefer_english_pivot: bool = True
    cache_size: int = 4096


@dataclass(slots=True)
class AudioConfig:
    source: str = "system"
    sample_rate: int = 16000
    frame_ms: int = 30


@dataclass(slots=True)
class VADConfig:
    backend: str = "silero"
    model_path: str = "models/silero_vad.onnx"
    start_threshold: float = 0.55
    end_threshold: float = 0.30
    min_speech_ms: int = 120
    min_silence_ms: int = 350
    preroll_ms: int = 200
    postroll_ms: int = 300


@dataclass(slots=True)
class ASRConfig:
    backend: str = "whisper_cpp"
    binary_path: str = "bin/whisper-sidecar"
    model: str = "models/ggml-large-v3-turbo-q5_0.bin"
    language: str = "auto"
    partial_interval_ms: int = 400
    final_silence_commit_ms: int = 700
    prompt_chars: int = 128
    max_chunk_ms: int = 6000
    threads: int = 4


@dataclass(slots=True)
class OverlayConfig:
    width_ratio: float = 0.45
    bottom_margin_px: int = 80
    max_lines: int = 2
    opacity: float = 0.85
    click_through: bool = True


@dataclass(slots=True)
class PlatformConfig:
    linux_overlay_backend: str = "auto"
    mac_capture_helper_socket: str = "/tmp/deep-caption-mac.sock"
    mac_capture_helper_path: str = "helpers/mac_audio_capture/.build/release/mac_audio_capture"


@dataclass(slots=True)
class Config:
    app: AppConfig = field(default_factory=AppConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    platform: PlatformConfig = field(default_factory=PlatformConfig)

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(
            app=AppConfig(**payload.get("app", {})),
            audio=AudioConfig(**payload.get("audio", {})),
            vad=VADConfig(**payload.get("vad", {})),
            asr=ASRConfig(**payload.get("asr", {})),
            translation=TranslationConfig(**payload.get("translation", {})),
            overlay=OverlayConfig(**payload.get("overlay", {})),
            platform=PlatformConfig(**payload.get("platform", {})),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Config":
        return cls(
            app=AppConfig(**payload.get("app", {})),
            audio=AudioConfig(**payload.get("audio", {})),
            vad=VADConfig(**payload.get("vad", {})),
            asr=ASRConfig(**payload.get("asr", {})),
            translation=TranslationConfig(**payload.get("translation", {})),
            overlay=OverlayConfig(**payload.get("overlay", {})),
            platform=PlatformConfig(**payload.get("platform", {})),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "app": asdict(self.app),
            "audio": asdict(self.audio),
            "vad": asdict(self.vad),
            "asr": asdict(self.asr),
            "translation": asdict(self.translation),
            "overlay": asdict(self.overlay),
            "platform": asdict(self.platform),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(self.as_dict(), sort_keys=False), encoding="utf-8")
