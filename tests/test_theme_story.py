"""Unit tests for theme, story, and timing (no ffmpeg render)."""

from __future__ import annotations

import unittest

from music_video.presets import UserCreativeInput, resolve_genre
from music_video.story import build_storyboard
from music_video.theme import build_theme
from music_video.timing import expand_shots


LYRICS = """[Verse 1]
love and lonely nights
[Chorus]
dance until we rise
[Outro]
goodbye
"""


class ThemeStoryTests(unittest.TestCase):
    def test_genre_alias(self):
        self.assertEqual(resolve_genre("hip hop").name, "hip-hop")
        self.assertEqual(resolve_genre("lo-fi").name, "lofi")

    def test_theme_from_lyrics(self):
        theme = build_theme("pop", LYRICS)
        self.assertEqual(theme.genre, "pop")
        self.assertIn("love", theme.lyric_moods)
        self.assertGreater(theme.speed, 0)

    def test_user_overrides(self):
        user = UserCreativeInput(
            theme="cyber rain",
            story="chase through flooded streets",
            speed=0.5,
            mood="melancholy neon",
        )
        theme = build_theme("edm", LYRICS, user)
        self.assertEqual(theme.speed, 0.5)
        self.assertEqual(theme.user_theme, "cyber rain")
        self.assertIn("melancholy", theme.mood)
        board = build_storyboard(LYRICS, theme, duration=60.0, user=user)
        self.assertEqual(board.arc, "custom")
        self.assertIn("chase", board.synopsis)
        self.assertGreaterEqual(len(board.scenes), 3)
        self.assertAlmostEqual(board.scenes[-1].end, 60.0, places=1)

    def test_timing_subdivides_with_speed(self):
        slow = build_theme("ambient", LYRICS, UserCreativeInput(speed=0.5))
        fast = build_theme("punk", LYRICS, UserCreativeInput(speed=2.0))
        board_s = build_storyboard(LYRICS, slow, 30.0)
        board_f = build_storyboard(LYRICS, fast, 30.0)
        shots_s = expand_shots(board_s, slow, bpm=80)
        shots_f = expand_shots(board_f, fast, bpm=160)
        self.assertGreater(len(shots_f), len(shots_s))


if __name__ == "__main__":
    unittest.main()
