"""Validate Find Me storyboard plan structure."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "examples/find_me/scene_plan.json"


class FindMePlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = json.loads(PLAN.read_text())

    def test_scene_count_and_kinds(self):
        scenes = self.plan["scenes"]
        self.assertEqual(len(scenes), 28)
        self.assertEqual(self.plan["scene_count"], 28)
        kinds = [s["kind"] for s in scenes]
        self.assertEqual(kinds.count("star"), 9)
        self.assertEqual(kinds.count("supporting"), 6)
        self.assertEqual(kinds.count("world"), 13)

    def test_master_frames_cover_all(self):
        covered = set()
        for mf in self.plan["master_frames"]:
            covered.update(mf["scenes"])
        self.assertEqual(covered, set(range(1, 29)))

    def test_files_unique_and_timed(self):
        files = [s["file"] for s in self.plan["scenes"]]
        self.assertEqual(len(files), len(set(files)))
        self.assertAlmostEqual(self.plan["scenes"][0]["t_start"], 0.0)
        self.assertAlmostEqual(self.plan["scenes"][-1]["t_end"], 204.0)
        for prev, cur in zip(self.plan["scenes"], self.plan["scenes"][1:]):
            self.assertLessEqual(prev["t_end"], cur["t_start"] + 0.01)

    def test_style_bible_and_lyrics_exist(self):
        self.assertTrue((ROOT / "examples/find_me/STYLE_BIBLE.txt").exists())
        self.assertTrue((ROOT / "examples/find_me/lyrics.txt").exists())
        heroes = list((ROOT / "assets/find_me/hero").glob("hero_*.*"))
        self.assertGreaterEqual(len(heroes), 2)


if __name__ == "__main__":
    unittest.main()
