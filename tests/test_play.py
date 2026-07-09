"""Tests for CLI play helpers."""

from __future__ import annotations

import importlib.util
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAY_PATH = ROOT / "python" / "play.py"

sys.path.insert(0, str(ROOT / "python"))
spec = importlib.util.spec_from_file_location("play_module_for_tests", PLAY_PATH)
play = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(play)


def test_quit_save_defaults_to_save_dir(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")

    path = play._quit_with_save(None, "Ironclad", "seed123")

    assert path is not None
    assert path.startswith(play.SAVE_DIR)
    assert path.endswith(".save")


def test_writeback_treats_disconnect_after_file_write_as_success(tmp_path):
    save_path = tmp_path / "run.save"

    def send(_cmd):
        save_path.write_text('{"ok":true}', encoding="utf-8")
        raise BrokenPipeError()

    assert play._writeback_continue_save(send, str(save_path)) is True


def test_writeback_treats_eof_after_file_write_as_success(tmp_path):
    save_path = tmp_path / "run.save"

    def send(_cmd):
        save_path.write_text('{"ok":true}', encoding="utf-8")
        return None

    assert play._writeback_continue_save(send, str(save_path)) is True


def test_writeback_disconnect_without_file_change_is_unknown(tmp_path):
    save_path = tmp_path / "run.save"
    save_path.write_text("old", encoding="utf-8")

    def send(_cmd):
        raise BrokenPipeError()

    assert play._writeback_continue_save(send, str(save_path), confirm_timeout=0) is None


def test_writeback_disconnect_with_existing_unchanged_save_is_unknown(tmp_path):
    save_path = tmp_path / "run.save"
    save_path.write_text('{"players":[]}', encoding="utf-8")

    def send(_cmd):
        return None

    assert play._writeback_continue_save(send, str(save_path), confirm_timeout=0) is None


def test_confirmed_save_path_requires_same_readable_save(tmp_path):
    save_path = tmp_path / "run.save"
    save_path.write_text('{"players":[]}', encoding="utf-8")

    assert play._is_confirmed_save_path(str(save_path), str(save_path)) is True
    assert play._is_confirmed_save_path(str(save_path), str(tmp_path / "other.save")) is False

    save_path.write_text("not json", encoding="utf-8")
    assert play._is_confirmed_save_path(str(save_path), str(save_path)) is False
