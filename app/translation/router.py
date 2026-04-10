from dataclasses import dataclass
from collections import OrderedDict

from app.config import TranslationConfig
from app.translation.argos_backend import ArgosTranslator
from app.translation.base import Translator


@dataclass(slots=True)
class TranslationRouter:
    config: TranslationConfig
    argos: Translator
    opus: Translator | None = None
    nllb: Translator | None = None
    _cache: OrderedDict[tuple[str, str, str], str] | None = None

    @classmethod
    def build_default(cls, config: TranslationConfig) -> "TranslationRouter":
        return cls(config=config, argos=ArgosTranslator(), _cache=OrderedDict())

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        normalized = " ".join(text.split())
        if not normalized:
            return ""
        if source_lang == target_lang:
            return normalized
        key = (source_lang, target_lang, normalized)
        if self._cache is not None and key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        backend = self.config.backend
        if backend == "argos":
            translated = self.argos.translate(normalized, source_lang, target_lang).strip()
            return self._remember(key, translated)
        if backend == "opus":
            if self.opus is None:
                raise RuntimeError("OPUS backend not configured")
            translated = self.opus.translate(normalized, source_lang, target_lang).strip()
            return self._remember(key, translated)
        if backend == "quality":
            if self.config.nllb_enabled and self.nllb is not None:
                translated = self.nllb.translate(normalized, source_lang, target_lang).strip()
                return self._remember(key, translated)
            translated = self.argos.translate(normalized, source_lang, target_lang).strip()
            return self._remember(key, translated)
        if backend == "auto":
            if self.opus is not None:
                try:
                    translated = self.opus.translate(normalized, source_lang, target_lang).strip()
                    return self._remember(key, translated)
                except Exception:
                    pass
            translated = self.argos.translate(normalized, source_lang, target_lang).strip()
            return self._remember(key, translated)
        raise ValueError(f"Unsupported translation backend: {backend}")

    def _remember(self, key: tuple[str, str, str], value: str) -> str:
        if self._cache is None:
            return value
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self.config.cache_size:
            self._cache.popitem(last=False)
        return value
