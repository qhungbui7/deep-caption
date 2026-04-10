from lingua import Language, LanguageDetectorBuilder


class LanguageDetector:
    def __init__(self) -> None:
        self._detector = LanguageDetectorBuilder.from_all_languages().build()

    def detect(self, text: str, fallback: str = "en") -> str:
        if len(text.strip()) < 2:
            return fallback
        result = self._detector.detect_language_of(text)
        if result is None:
            return fallback
        return _to_iso_code(result, fallback=fallback)


def _to_iso_code(language: Language, fallback: str) -> str:
    try:
        return language.iso_code_639_1.name.lower()
    except Exception:
        return fallback
