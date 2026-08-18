import json

from kofinmenu.discover import (
    discover_libraries,
    expand_add_choices,
    parse_root_item,
    synced_pairs,
)


def test_parse_root_item_keeps_movies():
    item = {
        "label": "Kids",
        "file": "plugin://plugin.video.kofin/?mode=browse&view=abc&type=movies",
    }
    parsed = parse_root_item(item)
    assert parsed["library_id"] == "abc"
    assert parsed["media"] == "movies"
    assert parsed["name"] == "Kids"


def test_parse_root_item_skips_continue_watching():
    item = {
        "label": "Continue watching",
        "file": "plugin://plugin.video.kofin/?mode=continuewatching",
    }
    assert parse_root_item(item) is None


def test_parse_mixed_children():
    item = {
        "label": "Mix",
        "file": "plugin://plugin.video.kofin/?mode=browse&view=mix1&type=mixed&folder=children",
    }
    parsed = parse_root_item(item)
    assert parsed["media"] == "mixed"
    choices = expand_add_choices([dict(parsed, synced=False)])
    assert [c["media"] for c in choices] == ["movies", "tvshows"]


def _rpc(monkeypatch, handler):
    import xbmc

    def execute(raw):
        req = json.loads(raw)
        return json.dumps(handler(req["method"], req.get("params") or {}))

    monkeypatch.setattr(xbmc, "executeJSONRPC", execute)


def test_discover_ok(kodi_fs, monkeypatch):
    def handler(method, params):
        if method == "Addons.GetAddonDetails":
            return {"result": {"addon": {"enabled": True}}}
        directory = params.get("directory", "")
        if directory == "plugin://plugin.video.kofin/":
            return {
                "result": {
                    "files": [
                        {
                            "label": "Kids",
                            "file": "plugin://plugin.video.kofin/?mode=browse&view=abc&type=movies",
                        },
                        {
                            "label": "Settings",
                            "file": "plugin://plugin.video.kofin/?mode=settings",
                        },
                    ]
                }
            }
        if directory == "library://video/kofin/":
            return {
                "result": {
                    "files": [
                        {
                            "label": "Kids",
                            "file": "library://video/kofin/kofinmoviesabc/",
                        }
                    ]
                }
            }
        return {"result": {"files": []}}

    _rpc(monkeypatch, handler)
    reason, libs = discover_libraries()
    assert reason == "ok"
    assert libs[0]["synced"] is True
    assert libs[0]["library_id"] == "abc"


def test_discover_missing(kodi_fs, monkeypatch):
    def handler(method, params):
        return {"error": {"message": "not found"}}

    _rpc(monkeypatch, handler)
    reason, libs = discover_libraries()
    assert reason == "kofin_missing"
    assert libs == []


def test_discover_not_logged_in(kodi_fs, monkeypatch):
    def handler(method, params):
        if method == "Addons.GetAddonDetails":
            return {"result": {"addon": {"enabled": True}}}
        return {
            "result": {
                "files": [
                    {
                        "label": "Settings",
                        "file": "plugin://plugin.video.kofin/?mode=settings",
                    }
                ]
            }
        }

    _rpc(monkeypatch, handler)
    reason, libs = discover_libraries()
    assert reason == "not_logged_in"


def test_synced_pairs_from_folder_names(kodi_fs, monkeypatch):
    def handler(method, params):
        return {
            "result": {
                "files": [
                    {"file": "library://video/kofin/kofintvshows99/"},
                    {"file": "library://video/kofin/index.xml"},
                ]
            }
        }

    _rpc(monkeypatch, handler)
    assert synced_pairs() == {("99", "tvshows")}
