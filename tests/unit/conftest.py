"""Put the addon ``lib/`` on sys.path the same way default.py does."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


STUB = """<?xml version="1.0" encoding="UTF-8"?>
<includes>
	<include name="KofinGeneratedSections">
		<!-- stub: no generated sections -->
	</include>
	<include name="KofinGeneratedMovieMenuItems">
		<!-- stub: no generated movie items -->
	</include>
	<include name="KofinGeneratedShowMenuItems">
		<!-- stub: no generated show items -->
	</include>
</includes>
"""


@pytest.fixture
def kodi_fs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    profile = tmp_path / "profile"
    xml_dir = home / "addons" / "skin.contuary" / "xml"
    xml_dir.mkdir(parents=True)
    (profile / "addon_data" / "script.skin.contuary").mkdir(parents=True)
    (xml_dir / "Includes.xml").write_text(
        '<includes>\n\t<include file="Includes_KofinGenerated.xml" />\n</includes>\n',
        encoding="utf-8",
    )
    (xml_dir / "Includes_KofinGenerated.xml").write_text(STUB, encoding="utf-8")

    mapping = {
        "special://home": home,
        "special://profile": profile,
    }

    def translate(path):
        for prefix, dest in mapping.items():
            if path == prefix:
                return str(dest)
            if path.startswith(prefix + "/"):
                return str(dest / path[len(prefix) + 1 :])
        return str(tmp_path / path.replace("special://", "").strip("/"))

    import xbmc
    import xbmcgui
    import xbmcvfs

    monkeypatch.setattr(xbmcvfs, "translatePath", translate)
    monkeypatch.setattr(xbmc, "executebuiltin", lambda *_a, **_k: None)
    monkeypatch.setattr(xbmc, "executeJSONRPC", lambda *_a, **_k: '{"result":{}}')
    monkeypatch.setattr(xbmc, "log", lambda *_a, **_k: None)

    store = {}

    class FakeWindow:
        def __init__(self, _wid=0):
            pass

        def getProperty(self, key):
            return store.get(key, "")

        def setProperty(self, key, value):
            store[key] = value

    class FakeDialog:
        def notification(self, *args, **kwargs):
            return None

        def select(self, *args, **kwargs):
            return -1

        def yesno(self, *args, **kwargs):
            return False

        def input(self, *args, **kwargs):
            return ""

        def browse(self, *args, **kwargs):
            return ""

        def ok(self, *args, **kwargs):
            return True

    monkeypatch.setattr(xbmcgui, "Window", FakeWindow)
    monkeypatch.setattr(xbmcgui, "Dialog", FakeDialog)
    return {"home": home, "profile": profile, "xml": xml_dir, "store": store}
