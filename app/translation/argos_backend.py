from functools import lru_cache

from app.translation.base import Translator


class ArgosTranslator(Translator):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        text = text.strip()
        if not text:
            return ""
        try:
            return _translate_cached(text, source_lang, target_lang)
        except Exception:
            return text


@lru_cache(maxsize=4096)
def _translate_cached(text: str, source_lang: str, target_lang: str) -> str:
    import argostranslate.translate

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((lang for lang in installed_languages if lang.code == source_lang), None)
    to_lang = next((lang for lang in installed_languages if lang.code == target_lang), None)
    if from_lang is None or to_lang is None:
        return text
    pair = from_lang.get_translation(to_lang)
    if pair is None:
        return text
    return pair.translate(text)
