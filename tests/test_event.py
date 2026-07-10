"""Tests for events."""
import pytest


class TestNeowEvent:
    def test_neow_is_first_event(self, game):
        state = game.start(seed="ne1")
        assert state["decision"] == "event_choice"
        assert "Neow" in str(state.get("event_name", ""))

    def test_neow_options(self, game):
        state = game.start(seed="ne2")
        for opt in state["options"]:
            assert "title" in opt
            assert isinstance(opt["title"], str)
            assert "is_locked" in opt

    def test_neow_option_vars(self, game):
        state = game.start(seed="ne3")
        for opt in state["options"]:
            if opt.get("vars"):
                for k, v in opt["vars"].items():
                    assert isinstance(v, (int, float))

    def test_choose_neow(self, game):
        state = game.start(seed="ne4")
        opts = [o for o in state["options"] if not o.get("is_locked")]
        state = game.act("choose_option", option_index=opts[0]["index"])
        assert state.get("decision") is not None


class TestEventDescriptions:
    def test_no_ismultiplayer_tag(self, game):
        state = game.start(seed="ed1")
        for opt in state.get("options", []):
            d = opt.get("description") or ""
            assert "IsMultiplayer" not in d

    def test_event_option_description_vars_are_localized(self, game):
        state = game.start(seed="tea-master", lang="zh")
        game.skip_neow(state)
        game.set_player(gold=414)
        state = game.enter_room("event", event="TEA_MASTER")

        assert state["decision"] == "event_choice"
        values = [
            str(value)
            for opt in state.get("options", [])
            for value in (opt.get("vars") or {}).values()
        ]
        assert values
        assert all(".description" not in value for value in values)

    def test_future_of_potions_option_vars(self, game):
        state = game.start(character="Necrobinder", seed="future-potions", lang="zh")
        game.skip_neow(state)
        game.set_player(potions=["BLOCK_POTION", "SNECKO_OIL", "DOOM_POTION"])
        state = game.enter_room("event", event="THE_FUTURE_OF_POTIONS")

        assert state["decision"] == "event_choice"
        assert state["options"]
        for option in state["options"]:
            assert {"Potion", "Rarity", "Type"} <= set(option["vars"] or {})
