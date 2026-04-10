from __future__ import annotations

from dataclasses import dataclass
import multiprocessing as mp
from pathlib import Path
from queue import Empty
import sys
from typing import Any

from app.asr.whisper_cpp import WhisperCppASR
from app.audio.segmenter import SpeechSegmenter
from app.capture.linux.pipewire_capture import PipeWireCapture
from app.capture.linux.pulseaudio_capture import PulseAudioCapture
from app.capture.mac.bridge_client import MacBridgeClient
from app.config import Config
from app.models import TranslationSegment
from app.translation.language_detect import LanguageDetector
from app.translation.router import TranslationRouter


@dataclass(slots=True)
class VoiceRuntimeController:
    config: Config
    target_lang: str
    source_id: str = ""
    _ctx: Any = None
    _cmd_q: Any = None
    _transcript_q: Any = None
    _out_q: Any = None
    _audio_proc: Any = None
    _translation_proc: Any = None

    def start(self) -> None:
        if self._audio_proc is not None:
            return
        self._ctx = mp.get_context("spawn")
        self._cmd_q = self._ctx.Queue()
        self._transcript_q = self._ctx.Queue()
        self._out_q = self._ctx.Queue()

        payload = self.config.as_dict()
        self._audio_proc = self._ctx.Process(
            target=_audio_worker,
            args=(payload, self.source_id, self._cmd_q, self._transcript_q),
            daemon=True,
        )
        self._translation_proc = self._ctx.Process(
            target=_translation_worker,
            args=(payload, self.target_lang, self._cmd_q, self._transcript_q, self._out_q),
            daemon=True,
        )
        self._audio_proc.start()
        self._translation_proc.start()

    def stop(self) -> None:
        if self._cmd_q is not None:
            self._cmd_q.put({"kind": "shutdown"})
        for proc in (self._audio_proc, self._translation_proc):
            if proc is None:
                continue
            proc.join(timeout=1.0)
            if proc.is_alive():
                proc.terminate()
        self._audio_proc = None
        self._translation_proc = None
        self._cmd_q = None
        self._transcript_q = None
        self._out_q = None
        self._ctx = None

    def poll(self, max_items: int = 8) -> list[TranslationSegment]:
        items: list[TranslationSegment] = []
        if self._out_q is None:
            return items
        for _ in range(max_items):
            try:
                payload = self._out_q.get_nowait()
            except Empty:
                break
            items.append(
                TranslationSegment(
                    source_text=str(payload["source_text"]),
                    translated_text=str(payload["translated_text"]),
                    source_lang=str(payload["source_lang"]),
                    target_lang=str(payload["target_lang"]),
                    t0_ms=int(payload["t0_ms"]),
                    t1_ms=int(payload["t1_ms"]),
                    is_final=bool(payload["is_final"]),
                )
            )
        return items


def _audio_worker(
    config_payload: dict[str, Any],
    source_id: str,
    cmd_q: Any,
    transcript_q: Any,
) -> None:
    config = Config.from_dict(config_payload)
    capture = _build_capture(config, source_id)
    vad = SpeechSegmenter(
        config.vad,
        sample_rate=config.audio.sample_rate,
        partial_interval_ms=config.asr.partial_interval_ms,
        max_chunk_ms=config.asr.max_chunk_ms,
    )
    asr = WhisperCppASR(config.asr)
    try:
        capture.start()
    except Exception:
        capture = PulseAudioCapture(
            sample_rate=config.audio.sample_rate,
            frame_ms=config.audio.frame_ms,
            source_id=source_id,
        )
        capture.start()
    try:
        while True:
            cmd = _poll_cmd(cmd_q)
            if cmd and cmd.get("kind") == "shutdown":
                break
            frame = capture.read()
            for chunk in vad.feed(frame):
                segment = asr.transcribe(chunk, prompt="")
                if not segment.text.strip():
                    continue
                transcript_q.put(
                    {
                        "text": segment.text,
                        "source_lang": segment.language,
                        "t0_ms": segment.t0_ms,
                        "t1_ms": segment.t1_ms,
                        "is_final": segment.is_final,
                    }
                )
    finally:
        capture.stop()


def _translation_worker(
    config_payload: dict[str, Any],
    target_lang: str,
    cmd_q: Any,
    transcript_q: Any,
    out_q: Any,
) -> None:
    config = Config.from_dict(config_payload)
    router = TranslationRouter.build_default(config.translation)
    detector = LanguageDetector()
    effective_target = target_lang
    while True:
        cmd = _poll_cmd(cmd_q)
        if cmd:
            kind = cmd.get("kind")
            if kind == "shutdown":
                break
            if kind == "set_target_lang":
                effective_target = str(cmd.get("target_lang", effective_target))
        try:
            transcript = transcript_q.get(timeout=0.1)
        except Empty:
            continue
        src_text = str(transcript["text"]).strip()
        if not src_text:
            continue
        source_lang = str(transcript.get("source_lang", "und"))
        if source_lang in {"", "und"}:
            source_lang = detector.detect(src_text, fallback="en")
        if bool(transcript.get("is_final", False)):
            translated = router.translate(src_text, source_lang=source_lang, target_lang=effective_target)
        else:
            translated = ""
        out_q.put(
            {
                "source_text": src_text,
                "translated_text": translated,
                "source_lang": source_lang,
                "target_lang": effective_target,
                "t0_ms": int(transcript["t0_ms"]),
                "t1_ms": int(transcript["t1_ms"]),
                "is_final": bool(transcript["is_final"]),
            }
        )


def _build_capture(config: Config, source_id: str):  # type: ignore[no-untyped-def]
    if sys.platform == "darwin":
        socket_path = config.platform.mac_capture_helper_socket
        helper_path = config.platform.mac_capture_helper_path
        return MacBridgeClient(
            socket_path=Path(socket_path),
            source_id=source_id,
            helper_path=Path(helper_path),
        )

    try:
        return PipeWireCapture(
            sample_rate=config.audio.sample_rate,
            frame_ms=config.audio.frame_ms,
            source_id=source_id,
        )
    except Exception:
        return PulseAudioCapture(
            sample_rate=config.audio.sample_rate,
            frame_ms=config.audio.frame_ms,
            source_id=source_id,
        )


def _poll_cmd(cmd_q: Any) -> dict[str, Any] | None:
    try:
        cmd = cmd_q.get_nowait()
    except Empty:
        return None
    if not isinstance(cmd, dict):
        return None
    return cmd
