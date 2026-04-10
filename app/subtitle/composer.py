from app.models import TranscriptSegment, TranslationSegment


def compose_subtitle(
    transcript: TranscriptSegment,
    translated_text: str,
    target_lang: str,
) -> TranslationSegment:
    return TranslationSegment(
        source_text=transcript.text,
        translated_text=translated_text,
        source_lang=transcript.language,
        target_lang=target_lang,
        t0_ms=transcript.t0_ms,
        t1_ms=transcript.t1_ms,
        is_final=transcript.is_final,
    )
