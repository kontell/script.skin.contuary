from kofinmenu.paths import (
    DROP_DYNAMIC_TV_INPROGRESS,
    MEDIA_MOVIES,
    MEDIA_TVSHOWS,
    MODE_DYNAMIC,
    MODE_SYNCED,
    MOVIE_SETTING_KEYS,
    SHOW_SETTING_KEYS,
    all_listing_path,
    esc_label,
    kofin_folder_name,
    kofin_node,
    parse_kofin_folder,
    plugin_browse,
    slot_ids,
    widgets_for,
)

STOCK_MOVIE_KEYS = (
    "home_no_movies_categories_widget",
    "home_no_movies_inprogress_widget",
    "home_no_movies_recentlyadded_widget",
    "home_no_movies_unwatched_widget",
    "home_no_movies_random_widget",
    "home_no_movies_genres_widget",
    "home_no_movies_sets_widget",
)

STOCK_SHOW_KEYS = (
    "home_no_tvshows_categories_widget",
    "home_no_tvshows_inprogress_widget",
    "home_no_tvshows_recentlyaddedepisodes_widget",
    "home_no_tvshows_unwatched_widget",
    "home_no_tvshows_genres_widget",
    "home_no_tvshows_studios_widget",
)


def test_setting_keys_match_home_xml():
    assert MOVIE_SETTING_KEYS == STOCK_MOVIE_KEYS
    assert SHOW_SETTING_KEYS == STOCK_SHOW_KEYS


def test_plugin_urls_have_no_trailing_slash():
    url = plugin_browse("abc", "movies", "recent")
    assert url.startswith("plugin://plugin.video.kofin/?")
    assert not url.endswith("/")
    assert "folder=recent" in url
    assert "view=abc" in url
    assert "type=movies" in url


def test_library_urls_have_trailing_slash():
    assert kofin_node("abc", "movies").endswith("/")
    assert kofin_node("abc", "movies", "recent").endswith(".xml/")
    assert "kofinmoviesabc" in kofin_node("abc", "movies")


def test_parse_kofin_folder():
    assert parse_kofin_folder("kofinmoviesf137") == ("movies", "f137")
    assert parse_kofin_folder("kofintvshows99") == ("tvshows", "99")
    assert parse_kofin_folder("kofin") is None
    assert parse_kofin_folder("movies") is None


def test_movie_widgets_both_modes():
    synced = widgets_for(MEDIA_MOVIES, MODE_SYNCED, "abc")
    dynamic = widgets_for(MEDIA_MOVIES, MODE_DYNAMIC, "abc")
    assert [w["kind"] for w in synced] == [
        "categories",
        "inprogress",
        "recent",
        "unwatched",
        "random",
        "genres",
        "sets",
    ]
    assert [w["kind"] for w in dynamic] == [w["kind"] for w in synced]
    assert all(w["setting_key"] for w in synced)
    assert synced[0]["content_path"] == kofin_node("abc", "movies")
    assert dynamic[0]["content_path"] == plugin_browse("abc", "movies")
    assert "inprogress.xml/" in synced[1]["content_path"]
    assert dynamic[1]["content_path"].endswith("folder=inprogress")


def test_show_widgets_drop_dynamic_studios():
    synced = widgets_for(MEDIA_TVSHOWS, MODE_SYNCED, "abc", include_studios=True)
    dynamic = widgets_for(MEDIA_TVSHOWS, MODE_DYNAMIC, "abc", include_studios=True)
    assert [w["kind"] for w in synced][-1] == "studios"
    assert "studios" not in [w["kind"] for w in dynamic]
    assert any(w["kind"] == "unwatched" for w in dynamic)
    unwatched = next(w for w in synced if w["kind"] == "unwatched")
    assert unwatched["content_path"].endswith("Contuary/unwatched_tvshows_abc.xsp")
    assert unwatched["setting_key"] == "home_no_tvshows_unwatched_widget"
    recent = next(w for w in synced if w["kind"] == "recent")
    assert recent["setting_key"] == "home_no_tvshows_recentlyaddedepisodes_widget"


def test_show_widgets_drop_studios_when_no_profile_tree():
    synced = widgets_for(MEDIA_TVSHOWS, MODE_SYNCED, "abc", include_studios=False)
    assert "studios" not in [w["kind"] for w in synced]


def test_dynamic_tv_inprogress_flag():
    widgets = widgets_for(MEDIA_TVSHOWS, MODE_DYNAMIC, "abc")
    kinds = [w["kind"] for w in widgets]
    if DROP_DYNAMIC_TV_INPROGRESS:
        assert "inprogress" not in kinds
    else:
        assert "inprogress" in kinds


def test_esc_label_neutralizes_info():
    escaped = esc_label("$INFO[System.BuildVersion]")
    assert escaped.startswith("$$INFO[")
    assert escaped.count("$INFO[") == escaped.count("$$INFO[")
    assert "&amp;" in esc_label('Kids & "Fun"')
    assert "&quot;" in esc_label('Kids & "Fun"')


def test_slot_ids_scale():
    zero = slot_ids(0)
    one = slot_ids(1)
    assert zero["group"] == 30000
    assert one["group"] == 30100
    assert zero["random"] == 30024
    assert one["random"] == 30124
    assert zero["empty"] == 30050
    assert one["sets"] == 30126


def test_all_listing_path():
    assert all_listing_path("movies", "synced", "abc").endswith("all.xml/")
    assert "folder=all" in all_listing_path("movies", "dynamic", "abc")


def test_folder_name():
    assert kofin_folder_name("xyz", "tvshows") == "kofintvshowsxyz"
