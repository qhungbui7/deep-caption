import unittest

import numpy as np

from app.audio.segmenter import SpeechSegmenter
from app.config import VADConfig
from app.models import AudioFrame


class SpeechSegmenterTest(unittest.TestCase):
    def test_emits_final_chunk_after_silence(self) -> None:
        config = VADConfig(model_path="models/missing.onnx")
        segmenter = SpeechSegmenter(config=config, sample_rate=16000)
        frame_samples = int(16000 * 0.03)
        t = 0
        chunks = []

        for _ in range(8):
            speech = np.ones((frame_samples,), dtype=np.float32) * 0.2
            chunks.extend(segmenter.feed(AudioFrame(speech, 16000, t, t + 30, "test")))
            t += 30

        for _ in range(20):
            silence = np.zeros((frame_samples,), dtype=np.float32)
            chunks.extend(segmenter.feed(AudioFrame(silence, 16000, t, t + 30, "test")))
            t += 30

        finals = [chunk for chunk in chunks if chunk.is_final]
        self.assertEqual(len(finals), 1)
        self.assertGreater(finals[0].pcm.size, frame_samples)


if __name__ == "__main__":
    unittest.main()
