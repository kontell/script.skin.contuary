import re
import xml.etree.ElementTree as ET

from kofinmenu import config
from kofinmenu.generate import (
    COMMENT,
    render_includes,
    write_profile_artifacts,
)
from kofinmenu.paths import slot_ids


def _doc(*sections):
    return {"version": 1, "sections": list(sections)}


def _movie(sid="c0a1b2c3", library_id="f137", name="Kids Movies", mode="synced"):
    return {
        "id": sid,
        "library_id": library_id,
        "media": "movies",
        "mode": mode,
        "name": name,
        "name_source": "custom",
        "library_name": "Kids",
        "icon": "icons/sidemenu/movies.png",
        "icon_source": "stock",
        "enabled": True,
    }


def _show(sid="d4e5f607", library_id="aabb", name="Kids Shows", mode="dynamic"):
    return {
        "id": sid,
        "library_id": library_id,
        "media": "tvshows",
        "mode": mode,
        "name": name,
        "name_source": "custom",
        "library_name": "Kids TV",
        "icon": "icons/sidemenu/tv.png",
        "icon_source": "stock",
        "enabled": True,
    }


def _parse(text):
    return ET.fromstring(COMMENT.sub("", text))


def test_empty_doc_is_registered_stub(kodi_fs):
    text = render_includes(config.empty_doc())
    root = _parse(text)
    names = [child.get("name") for child in root]
    assert names == [
        "KofinGeneratedSections",
        "KofinGeneratedMovieMenuItems",
        "KofinGeneratedShowMenuItems",
    ]
    # After comment strip the include is empty — the file on disk still has
    # the comment child that LoadIncludes needs. Assert the source has it.
    assert "<!-- stub: no generated sections -->" in text


def test_one_movies_synced_and_one_shows_dynamic(kodi_fs):
    text = render_includes(_doc(_movie(), _show()))
    _parse(text)
    assert "library://video/kofin/kofinmoviesf137/" in text
    assert (
        "plugin://plugin.video.kofin/?mode=browse&amp;view=aabb&amp;type=tvshows"
        in text
    )
    assert "Library.HasContent" not in text
    assert "additional_movie_items" not in text
    assert "additional_tvshow_items" not in text
    assert 'name="label" value="Kids Movies"' in text
    assert '<property name="id">kofin0</property>' in text
    assert '<property name="id">kofin1</property>' in text
    # MainMenuTitle is the first include inside each grouplist.
    grouplist = text.split('<control type="grouplist" id="30001">', 1)[1]
    first_include = grouplist.split("<include content=", 1)[1]
    assert first_include.startswith('"MainMenuTitle"')
    assert "contuary_studios_" not in text  # dynamic show, no studios
    assert "home_no_tvshows_recentlyaddedepisodes_widget" in text
    assert "$NUMBER[30000]" in text
    assert "$NUMBER[30100]" in text


def test_two_movies_unique_ids(kodi_fs):
    text = render_includes(
        _doc(_movie(), _movie(sid="eeeeeeee", library_id="zzzz", name="Adult"))
    )
    assert 'id="30000"' in text
    assert 'id="30100"' in text
    assert 'value="30020"' in text
    assert 'value="30120"' in text
    assert slot_ids(1)["sets"] == 30126
    assert 'value="30126"' in text


def test_escape_name_and_info(kodi_fs):
    text = render_includes(_doc(_movie(name='Kids & "Fun" $INFO[System.BuildVersion]')))
    _parse(text)
    assert "Kids &amp; &quot;Fun&quot;" in text
    assert "$$INFO[" in text
    assert text.count("$INFO[") == text.count("$$INFO[")


def test_empty_state_imagewidget_uses_setting_keys(kodi_fs):
    text = render_includes(_doc(_movie()))
    assert 'content="ImageWidget"' in text
    assert 'name="button_id" value="30050"' in text
    assert "home_no_movies_categories_widget" in text
    assert "home_no_movies_inprogress_widget" in text
    assert "$LOCALIZE[31179]" in text
    assert "$LOCALIZE[186]" in text
    assert "visible_2" in text
    visible = text.split('name="visible" value="', 1)[1].split('"/>', 1)[0]
    assert visible.startswith("[!Skin.HasSetting(")
    assert "] + " in visible


def test_synced_tv_writes_xsp(kodi_fs):
    doc = _doc(_show(mode="synced", library_id="tv1"))
    write_profile_artifacts(doc)
    xsp = (
        kodi_fs["profile"]
        / "playlists"
        / "video"
        / "Contuary"
        / "unwatched_tvshows_tv1.xsp"
    )
    assert xsp.is_file()
    body = xsp.read_text(encoding="utf-8")
    _parse(body)
    assert "<value>Kids TV</value>" in body
    # No profile video tree in this fixture: no studios node.
    assert not (kodi_fs["profile"] / "library" / "video").exists()


def test_studios_node_only_if_video_tree_exists(kodi_fs):
    video = kodi_fs["profile"] / "library" / "video"
    video.mkdir(parents=True)
    doc = _doc(_show(mode="synced", library_id="tv1"))
    write_profile_artifacts(doc)
    node = video / "contuary_studios_tv1.xml"
    assert node.is_file()
    _parse(node.read_text(encoding="utf-8"))
    text = render_includes(doc)
    assert "library://video/contuary_studios_tv1.xml/" in text


def test_orphan_xsp_removed(kodi_fs):
    playlist = kodi_fs["profile"] / "playlists" / "video" / "Contuary"
    playlist.mkdir(parents=True)
    stale = playlist / "unwatched_tvshows_gone.xsp"
    stale.write_text("<smartplaylist/>", encoding="utf-8")
    write_profile_artifacts(_doc(_show(mode="synced", library_id="keep")))
    assert not stale.exists()
    assert (playlist / "unwatched_tvshows_keep.xsp").is_file()
