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


def test_potion_str_shows_slot_only_for_inventory_potions():
    assert play.potion_str({"name": "Dex Potion", "index": 2}) == "[2] Dex Potion"
    assert play.potion_str({"name": "Dex Potion"}) == "Dex Potion"


def test_upgrade_preview_merges_duplicate_damage_vars():
    parts = play._format_upgrade_preview(
        {"damage": 6, "ostydamage": 6},
        {"stats": {"damage": 9, "ostydamage": 9}},
    )

    assert parts is not None
    assert len(parts) == 1
    assert "6→9" in parts[0]


def test_upgrade_preview_keeps_different_stat_types():
    parts = play._format_upgrade_preview(
        {"damage": 6, "block": 6},
        {"stats": {"damage": 9, "block": 9}},
    )

    assert parts is not None
    assert len(parts) == 2


def test_format_description_resolves_nested_vars():
    text = play.format_description({
        "description": "支付{Cost}金币。{Effect}",
        "vars": {
            "Cost": 50,
            "Effect": "在你接下来的{Combats}场战斗开始时，升级你的初始手牌。",
            "Combats": 1,
        },
    })

    assert text == "支付50金币。在你接下来的1场战斗开始时，升级你的初始手牌。"


def test_show_event_resolves_title_vars(capsys):
    play.show_event({
        "event_name": "Test Event",
        "options": [{
            "index": 0,
            "title": "Insert {Rarity} Potion",
            "description": "Lose {Potion}.",
            "vars": {"Rarity": "Common", "Potion": "Block Potion"},
        }],
        "player": {},
    })

    output = capsys.readouterr().out
    assert "Insert Common Potion" in output
    assert "{Rarity}" not in output
