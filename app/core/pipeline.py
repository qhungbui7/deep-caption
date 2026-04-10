import time
from dataclasses import dataclass, field

from app.asr.prompt_manager import PromptManager
from app.events import ASREngine, VAD
from app.models import AudioFrame, TranslationSegment
from app.subtitle.composer import compose_subtitle
from app.subtitle.stabilizer import SubtitleStabilizer
from app.translation.language_detect import LanguageDetector
from app.translation.router import TranslationRouter


@dataclass(slots=True)
class TextTranslationPipeline:
    router: TranslationRouter
    detector: LanguageDetector = field(default_factory=LanguageDetector)

    def translate_text(self, text: str, target_lang: str) -> TranslationSegment | None:
        normalized = " ".join(text.split())
        if len(normalized) < 2:
            return None
        source_lang = self.detector.detect(normalized, fallback="en")
        translated = self.router.translate(
            normalized,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        t_ms = int(time.monotonic() * 1000)
        return TranslationSegment(
            source_text=normalized,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            t0_ms=t_ms,
            t1_ms=t_ms,
            is_final=True,
        )


@dataclass(slots=True)
class VoiceTranslationPipeline:
    router: TranslationRouter
    vad: VAD
    asr: ASREngine
    prompt_manager: PromptManager = field(default_factory=PromptManager)
    stabilizer: SubtitleStabilizer = field(default_factory=SubtitleStabilizer)

    def feed_frame(self, frame: AudioFrame, target_lang: str) -> list[TranslationSegment]:
        outputs: list[TranslationSegment] = []
        chunks = self.vad.feed(frame)
        for chunk in chunks:
            transcript = self.asr.transcribe(chunk, self.prompt_manager.get_prompt())
            stable = self.stabilizer.consume_final(transcript.text)
            if not stable.ready_for_translation:
                continue
            translated = self.router.translate(
                stable.text,
                source_lang=transcript.language,
                target_lang=target_lang,
            )
            segment = compose_subtitle(
                transcript=transcript,
                translated_text=translated,
                target_lang=target_lang,
            )
            outputs.append(segment)
            if segment.is_final:
                self.prompt_manager.commit(segment.source_text)
        return outputs
