class PromptManager:
    def __init__(self, max_chars: int = 128) -> None:
        self.max_chars = max_chars
        self._tail = ""

    def get_prompt(self) -> str:
        return self._tail

    def commit(self, text: str) -> None:
        merged = f"{self._tail} {text}".strip()
        self._tail = merged[-self.max_chars :]
