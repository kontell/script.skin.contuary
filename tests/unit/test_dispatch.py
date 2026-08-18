import sys

import default
from kofinmenu import config


def test_import_kofinmenu_via_default_sys_path():
    import kofinmenu.config
    import kofinmenu.generate

    assert kofinmenu.config.SCHEMA_VERSION == 1


def test_pick_mode_dynamic_only_does_not_need_dialog(kodi_fs):
    """Documentaries is unsynced: _pick_mode must resolve MODE_DYNAMIC."""
    from kofinmenu.ui import _pick_mode

    assert _pick_mode({"synced": False}) == "dynamic"


def test_pick_mode_synced_default_is_first_option(kodi_fs, monkeypatch):
    from kofinmenu import ui

    class FakeDialog:
        def select(self, heading, labels, **kwargs):
            assert labels[0].startswith("Synced")
            return 0

    monkeypatch.setattr(ui, "_dialog", lambda: FakeDialog())
    assert ui._pick_mode({"synced": True}) == "synced"


def test_sync_does_not_call_ensure(kodi_fs, monkeypatch):
    called = []
    monkeypatch.setattr(default, "ensure", lambda: called.append("ensure"))
    monkeypatch.setattr(
        default, "run_resolution", lambda arg: called.append("res:%s" % arg)
    )
    monkeypatch.setattr(sys, "argv", ["default.py", "_sync"])
    default.main()
    assert called == ["res:_sync"]
    assert "ensure" not in called


def test_ensure_is_recognised(kodi_fs, monkeypatch):
    called = []
    monkeypatch.setattr(default, "ensure", lambda: called.append("ensure"))
    monkeypatch.setattr(sys, "argv", ["default.py", "_ensure"])
    default.main()
    assert called == ["ensure"]


def test_kofinmenu_is_recognised(kodi_fs, monkeypatch):
    called = []
    monkeypatch.setattr(default, "run_manager", lambda: called.append("ui"))
    monkeypatch.setattr(sys, "argv", ["default.py", "kofinmenu"])
    default.main()
    assert called == ["ui"]


def test_unknown_falls_through_to_resolution(kodi_fs, monkeypatch):
    seen = []
    monkeypatch.setattr(default, "run_resolution", lambda arg: seen.append(arg))
    monkeypatch.setattr(sys, "argv", ["default.py", "nope"])
    default.main()
    assert seen == ["nope"]


def test_kofin_add_writes_json(kodi_fs, monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["default.py", "_kofin_add", "abc", "movies", "dynamic", "Kids"]
    )
    default.main()
    doc = config.load()
    assert len(doc["sections"]) == 1
    assert doc["sections"][0]["library_id"] == "abc"
    assert doc["sections"][0]["name"] == "Kids"
    generated = kodi_fs["xml"] / "Includes_KofinGenerated.xml"
    assert "Kids" in generated.read_text(encoding="utf-8")


def test_resolution_name_still_routed(kodi_fs, monkeypatch):
    seen = []
    monkeypatch.setattr(default, "run_resolution", lambda arg: seen.append(arg))
    monkeypatch.setattr(sys, "argv", ["default.py", "2256x1269"])
    default.main()
    assert seen == ["2256x1269"]
