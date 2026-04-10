def ensure_screen_recording_permission() -> bool:
    # ScreenCaptureKit will trigger the system permission prompt at runtime.
    return True
