"""Unit tests for fal helpers (no network)."""

from __future__ import annotations

import os

from music_video.fal_gen import fal_available, fal_key


def test_fal_key_reads_fal_key(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.delenv("FAL_API_KEY", raising=False)
    assert fal_key() is None
    assert fal_available() is False
    monkeypatch.setenv("FAL_KEY", "test-key")
    assert fal_key() == "test-key"
    assert fal_available() is True


def test_fal_key_reads_fal_api_key(monkeypatch):
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.setenv("FAL_API_KEY", "legacy-key")
    assert fal_key() == "legacy-key"
    assert fal_available() is True


def test_ramon_scene_plan_ratios():
    import json
    from pathlib import Path

    plan = json.loads(Path("examples/ramon/scene_plan.json").read_text())
    assert plan["scene_count"] == 24
    assert len(plan["scenes"]) == 24
    kinds = [s["kind"] for s in plan["scenes"]]
    assert kinds.count("star") == plan["starring_count"]
    assert abs(kinds.count("star") / 24 - 0.33) < 0.05
