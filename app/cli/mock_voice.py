from __future__ import annotations

import argparse
import time
import wave
from pathlib import Path

import numpy as np

from app.asr.whisper_cpp import WhisperCppASR
from app.audio.resample import resample_mono_float32
from app.audio.segmenter import SpeechSegmenter
from app.config import ASRConfig, Config
from app.core.pipeline import VoiceTranslationPipeline
from app.events import ASREngine
from app.models import AudioFrame, SpeechChunk, TranscriptSegment
from app.translation.router import TranslationRouter


class MockTranscriptASR(ASREngine):
    def __init__(self, transcript: str, language: str = "en") -> None:
        self.transcript = transcript.strip()
        self.language = language

    def transcribe(self, chunk: SpeechChunk, prompt: str) -> TranscriptSegment:
        text = self.transcript
        if not text:
            duration_s = max((chunk.t1_ms - chunk.t0_ms) / 1000.0, 0.1)
            text = f"[mock speech {duration_s:.1f}s]"
        return TranscriptSegment(
            text=text,
            language=self.language,
            t0_ms=chunk.t0_ms,
            t1_ms=chunk.t1_ms,
            is_final=chunk.is_final,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run voice translation pipeline from a WAV file.",
    )
    parser.add_argument("--wav", required=True, help="Path to source WAV file")
    parser.add_argument("--target-lang", default="vi", help="Target ISO language code")
    parser.add_argument(
        "--config",
        default=str(Path.home() / ".config" / "deep-caption" / "config.yaml"),
        help="Config YAML path",
    )
    parser.add_argument(
        "--mock-transcript",
        default="",
        help="Use this fixed transcript and skip whisper sidecar",
    )
    parser.add_argument(
        "--mock-source-lang",
        default="en",
        help="Source language code used with --mock-transcript",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Sleep per frame to simulate live processing",
    )
    args = parser.parse_args()

    config = Config.load(Path(args.config))
    wav_path = Path(args.wav)
    if not wav_path.exists():
        raise SystemExit(f"WAV file not found: {wav_path}")

    router = TranslationRouter.build_default(config.translation)
    segmenter = SpeechSegmenter(config=config.vad, sample_rate=config.audio.sample_rate)
    asr = _build_asr(config.asr, args.mock_transcript, args.mock_source_lang)
    pipeline = VoiceTranslationPipeline(router=router, vad=segmenter, asr=asr)

    frame_ms = config.audio.frame_ms
    emitted = 0
    last_t = 0
    for frame in iter_wav_frames(wav_path, sample_rate=config.audio.sample_rate, frame_ms=frame_ms):
        last_t = frame.t1_ms
        for translated in pipeline.feed_frame(frame, target_lang=args.target_lang):
            emitted += 1
            print(
                f"[{translated.t0_ms:>6}-{translated.t1_ms:<6}] "
                f"{translated.source_lang}->{translated.target_lang} | "
                f"{translated.source_text} => {translated.translated_text}"
            )
        if args.realtime:
            time.sleep(frame_ms / 1000.0)

    # Flush trailing speech with synthetic silence so final chunks are emitted.
    silence = np.zeros((int(config.audio.sample_rate * frame_ms / 1000),), dtype=np.float32)
    for idx in range(max(1, config.vad.min_silence_ms // frame_ms) + 1):
        t0 = last_t + (idx * frame_ms)
        t1 = t0 + frame_ms
        frame = AudioFrame(
            pcm=silence,
            sample_rate=config.audio.sample_rate,
            t0_ms=t0,
            t1_ms=t1,
            source_id="flush",
        )
        for translated in pipeline.feed_frame(frame, target_lang=args.target_lang):
            emitted += 1
            print(
                f"[{translated.t0_ms:>6}-{translated.t1_ms:<6}] "
                f"{translated.source_lang}->{translated.target_lang} | "
                f"{translated.source_text} => {translated.translated_text}"
            )
    print(f"Segments emitted: {emitted}")
    return 0


def _build_asr(asr_config: ASRConfig, mock_transcript: str, mock_source_lang: str) -> ASREngine:
    if mock_transcript.strip():
        return MockTranscriptASR(transcript=mock_transcript, language=mock_source_lang)
    return WhisperCppASR(asr_config)


def iter_wav_frames(path: Path, sample_rate: int, frame_ms: int) -> list[AudioFrame]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        src_rate = wav_file.getframerate()
        raw = wav_file.readframes(wav_file.getnframes())
    pcm16 = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        pcm16 = pcm16.reshape(-1, channels).mean(axis=1)
    mono = resample_mono_float32(pcm16, src_rate=src_rate, dst_rate=sample_rate)

    step = int(sample_rate * frame_ms / 1000)
    t_ms = 0
    frames: list[AudioFrame] = []
    for start in range(0, mono.size, step):
        chunk = mono[start : start + step]
        if chunk.size < step:
            chunk = np.pad(chunk, (0, step - chunk.size))
        frames.append(
            AudioFrame(
                pcm=chunk,
                sample_rate=sample_rate,
                t0_ms=t_ms,
                t1_ms=t_ms + frame_ms,
                source_id=path.name,
            )
        )
        t_ms += frame_ms
    return frames


if __name__ == "__main__":
    raise SystemExit(main())
