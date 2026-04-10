import os


def session_type() -> str:
    return os.environ.get("XDG_SESSION_TYPE", "unknown").lower()


def choose_overlay_backend(requested: str) -> str:
    if requested in {"x11", "wayland"}:
        return requested
    sess = session_type()
    if sess == "x11":
        return "x11"
    if sess == "wayland":
        return "wayland"
    return "x11"
