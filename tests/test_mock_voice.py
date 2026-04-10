import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from app.cli.mock_voice import iter_wav_frames


class MockVoiceCliTest(unittest.TestCase):
    def test_iter_wav_frames_uses_30ms_chunks(self) -> None:
        sample_rate = 16000
        duration_s = 1.0
        samples = int(sample_rate * duration_s)
        tone = (0.15 * np.sin(2 * np.pi * 220 * np.arange(samples) / sample_rate)).astype(np.float32)
        pcm16 = np.clip(tone * 32767.0, -32768, 32767).astype(np.int16)

        with tempfile.TemporaryDirectory() as temp_dir:
            wav_path = Path(temp_dir) / "sample.wav"
            with wave.open(str(wav_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm16.tobytes())

            frames = iter_wav_frames(wav_path, sample_rate=sample_rate, frame_ms=30)
            self.assertGreater(len(frames), 0)
            self.assertEqual(frames[0].t0_ms, 0)
            self.assertEqual(frames[0].t1_ms, 30)
            self.assertEqual(frames[-1].sample_rate, sample_rate)


if __name__ == "__main__":
    unittest.main()
