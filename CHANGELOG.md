# Changelog

All notable changes to this project are documented in this file.

## [0.3.0] - 2026-04-11

### Added
- `bin/whisper-sidecar` executable wrapper for whisper.cpp CLI output.
- Linux source discovery for PipeWire and PulseAudio sources.
- Capture adapters for PipeWire (`pw-cat`) and PulseAudio (`parec`) frame reads.
- macOS bridge protocol helpers (framed control + framed PCM decode) and bridge capture client.
- Multi-process voice runtime controller and `Supervisor` integration.
- Voice mode UI window with source picker, logs, tray actions, and hotkeys.
- Terminal live voice command: `deep-caption-voice`.
- Swift package scaffold for ScreenCaptureKit helper in `helpers/mac_audio_capture`.
- `deep-caption --config <path>` runtime config override for terminal-driven testing.

### Changed
- Added `platform` config section and overlay backend selection logic.
- Main app now supports `app.mode = voice` and Linux X11/Wayland overlay adapters.
- Overlay now tracks render states (`hidden`, `partial`, `final`, `fading`).
- macOS helper now runs a live ScreenCaptureKit audio stream loop and writes framed PCM packets over unix socket.
- macOS Python bridge now auto-launches helper binary and reconnects with retry logic.

## [0.2.0] - 2026-04-11

### Added
- Voice pipeline core modules: audio ring buffer, resampler, VAD adapter, speech segmenter.
- whisper.cpp ASR sidecar contract with WAV input and JSON parsing.
- Subtitle stabilizer/composer/history helpers.
- `VoiceTranslationPipeline` wired into shared core pipeline.
- `deep-caption-mock-voice` CLI for WAV-driven voice pipeline validation.
- Basic unit tests for segmenter, subtitle stabilizer, and WAV frame chunking.

### Changed
- Expanded config schema with `audio`, `vad`, and `asr` sections.
- Updated README with mock voice workflow and usage examples.
- Added translation router LRU-style cache with configurable size.

## [0.1.0] - 2026-04-11

### Added
- Initial app bootstrap for text translation mode.
- PySide6 transparent subtitle overlay and settings window.
- Argos-based translation backend with language detection and routing.
- Base project packaging (`pyproject.toml`) and default config file.
