from app.translation.base import Translator


class NllbTranslator(Translator):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        raise RuntimeError("NLLB backend is disabled by default")
