from dataclasses import dataclass


@dataclass(slots=True)
class OverlayTheme:
    background_rgba: str = "rgba(18, 18, 18, 217)"
    translated_text_color: str = "white"
    source_text_color: str = "#A3A3A3"
