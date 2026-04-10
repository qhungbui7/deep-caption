import unittest
from unittest.mock import patch

from app.capture.linux.source_discovery import _pulse_sources


class SourceDiscoveryTest(unittest.TestCase):
    @patch("subprocess.run")
    def test_pulse_sources_parsed(self, mock_run) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "42\talsa_output.pci.monitor\tmodule-alsa-card.c\tfloat32le 2ch 44100Hz\n"
        sources = _pulse_sources()
        self.assertGreaterEqual(len(sources), 1)
        self.assertTrue(any(src.id.startswith("pulse:") for src in sources))


if __name__ == "__main__":
    unittest.main()
