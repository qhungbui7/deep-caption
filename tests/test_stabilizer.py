import unittest

from app.subtitle.stabilizer import SubtitleStabilizer


class SubtitleStabilizerTest(unittest.TestCase):
    def test_partial_and_idle_commit(self) -> None:
        st = SubtitleStabilizer(idle_commit_ms=700)
        first = st.consume_partial("hello", now_ms=100)
        self.assertFalse(first.ready_for_translation)
        self.assertIsNone(st.maybe_commit_idle(500))
        idle = st.maybe_commit_idle(900)
        self.assertIsNotNone(idle)
        assert idle is not None
        self.assertTrue(idle.ready_for_translation)


if __name__ == "__main__":
    unittest.main()
