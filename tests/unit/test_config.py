import pytest

from kofinmenu import config


def _section(**overrides):
    base = {
        "id": "aaaa1111",
        "library_id": "lib1",
        "media": "movies",
        "mode": "synced",
        "name": "Kids",
        "name_source": "library",
        "library_name": "Kids",
        "icon": "icons/sidemenu/movies.png",
        "icon_source": "stock",
        "enabled": True,
    }
    base.update(overrides)
    return base


def test_round_trip(kodi_fs):
    doc = config.empty_doc()
    config.add_section(doc, _section())
    config.save(doc)
    loaded = config.load()
    assert loaded["sections"][0]["library_id"] == "lib1"
    assert loaded["sections"][0]["name"] == "Kids"


def test_reject_duplicate_library(kodi_fs):
    doc = config.empty_doc()
    config.add_section(doc, _section())
    with pytest.raises(config.ConfigError):
        config.add_section(doc, _section(id="bbbb2222"))


def test_allow_same_id_different_media(kodi_fs):
    doc = config.empty_doc()
    config.add_section(doc, _section())
    config.add_section(
        doc,
        _section(id="bbbb2222", media="tvshows", icon="icons/sidemenu/tv.png"),
    )
    assert len(doc["sections"]) == 2


def test_reject_ninth(kodi_fs):
    doc = config.empty_doc()
    for i in range(8):
        config.add_section(
            doc,
            _section(id="%08d" % i, library_id="lib%d" % i),
        )
    with pytest.raises(config.ConfigError):
        config.add_section(doc, _section(id="99999999", library_id="lib9"))


def test_unknown_version_refused(kodi_fs):
    with pytest.raises(config.ConfigError):
        config.validate({"version": 99, "sections": []})


def test_remove_and_move(kodi_fs):
    doc = config.empty_doc()
    config.add_section(doc, _section(id="aaaa1111", library_id="a"))
    config.add_section(doc, _section(id="bbbb2222", library_id="b", name="B"))
    config.move_section(doc, "bbbb2222", -1)
    assert [s["id"] for s in doc["sections"]] == ["bbbb2222", "aaaa1111"]
    config.remove_section(doc, "aaaa1111")
    assert [s["id"] for s in doc["sections"]] == ["bbbb2222"]


def test_set_name_marks_custom(kodi_fs):
    doc = config.empty_doc()
    config.add_section(doc, _section())
    config.set_field(doc, "aaaa1111", "name", "Custom")
    assert doc["sections"][0]["name"] == "Custom"
    assert doc["sections"][0]["name_source"] == "custom"
