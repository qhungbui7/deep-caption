import re


_MULTI_SPACE = re.compile(r"\s+")


def normalize_transcript(text: str) -> str:
    cleaned = text.strip()
    cleaned = _MULTI_SPACE.sub(" ", cleaned)
    return cleaned
