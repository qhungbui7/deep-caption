import unittest

from app.platform.linux_env import choose_overlay_backend


class LinuxEnvTest(unittest.TestCase):
    def test_choose_overlay_backend_respects_explicit(self) -> None:
        self.assertEqual(choose_overlay_backend("x11"), "x11")
        self.assertEqual(choose_overlay_backend("wayland"), "wayland")


if __name__ == "__main__":
    unittest.main()
