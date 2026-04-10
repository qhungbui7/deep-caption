# deep-caption

Offline subtitle overlay app for games, videos, and desktop audio.

This repository currently implements **Phase 1 + core Phase 2/3 runtime wiring**:

- Text input -> language detect -> translation -> subtitle overlay
- Argos-based translation backend with pluggable router interface
- Transparent, always-on-top PySide6 subtitle window
- Settings controls for target language and source text visibility
- Audio ring buffer + Silero-ONNX/fallback VAD adapter + speech segmenter
- whisper.cpp sidecar contract (`wav` in, JSON out) and subtitle stabilizer helpers
- Multi-process voice runtime supervisor (audio/asr process + translation process + UI process)
- Linux capture adapters (PipeWire first, Pulse fallback)
- macOS Unix-socket bridge client contract for ScreenCaptureKit helper
- Voice mode window, tray controls, source picker, logs, and hotkeys

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
deep-caption --config ./config/default.yaml
```

## Mock voice pipeline runner

You can validate the voice pipeline from a WAV file without platform capture:

```bash
deep-caption-mock-voice --wav /path/to/sample.wav --target-lang vi --mock-transcript "hello world"
```

If you have a working whisper sidecar + model configured, omit `--mock-transcript`:

```bash
deep-caption-mock-voice --wav /path/to/sample.wav --target-lang vi
```

## Live voice runner

Use voice mode UI:

```bash
deep-caption --config ./config/default.yaml
```

Then set `app.mode: voice` in your config file.

Or use terminal runner:

```bash
deep-caption-voice --target-lang vi
```

## Current layout

```text
app/
  main.py
  config.py
  models.py
  core/pipeline.py
  audio/
    ring_buffer.py
    vad.py
    segmenter.py
  asr/
    whisper_cpp.py
    prompt_manager.py
  subtitle/
    stabilizer.py
    composer.py
  overlay/qt_overlay.py
  translation/
    base.py
    argos_backend.py
    language_detect.py
    router.py
  ui/
    settings_window.py
    text_mode_window.py
```

## Notes

- The app defaults to text mode for now.
- Voice mode building blocks are in place, but capture adapters and sidecar binary are still required.
- Build `helpers/mac_audio_capture` on macOS and wire ScreenCaptureKit packet streaming.
- Build helper once on macOS:
  - `cd helpers/mac_audio_capture && swift build -c release`
- Ensure `bin/whisper-sidecar` can find a built `whisper-cli` binary (`vendor/whisper.cpp/...` or PATH).
- Argos model packages must be installed for your language pairs.
- See `CHANGELOG.md` for implementation history.
