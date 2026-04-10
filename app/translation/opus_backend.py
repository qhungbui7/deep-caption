from app.translation.base import Translator


class OpusTranslator(Translator):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        raise RuntimeError("OPUS backend is not configured yet")
