"""Frozen Movies/Shows widget map for generated kofin home sections.

Every ``setting_key`` is the literal from Home.xml / Includes_SettingsDialog.xml.
Plugin browse URLs have no trailing slash (kofin strips one query character).
Library node URLs have a trailing slash.
"""

from xml.sax.saxutils import escape as xml_escape

KOFIN = "plugin://plugin.video.kofin/"
MAX_SECTIONS = 8
GENERATOR_VERSION = 1

MEDIA_MOVIES = "movies"
MEDIA_TVSHOWS = "tvshows"
MODE_SYNCED = "synced"
MODE_DYNAMIC = "dynamic"

STOCK_ICON = {
    MEDIA_MOVIES: "icons/sidemenu/movies.png",
    MEDIA_TVSHOWS: "icons/sidemenu/tv.png",
}

# Live probe on Piers/LibreELEC 2026-08-18: folder=inprogress for tvshows
# returned 0 items (node_query is implemented but the TV node menu does not
# expose it, and the listing was empty). Synced inprogress.xml is shows and
# stays. Flip back if a later kofin build returns series here.
DROP_DYNAMIC_TV_INPROGRESS = True

_ATTR = {'"': "&quot;", "'": "&apos;"}


def esc_xml(value):
    return xml_escape(value or "", _ATTR)


def esc_label(value):
    """Neutralize skin $INFO / $VAR / $LOCALIZE injection in baked labels."""
    return esc_xml((value or "").replace("$", "$$"))


def plugin_browse(library_id, media, folder=None):
    query = "mode=browse&view=%s&type=%s" % (library_id, media)
    if folder:
        query += "&folder=%s" % folder
    return KOFIN + "?" + query


def kofin_folder_name(library_id, media):
    return "kofin%s%s" % (media, library_id)


def kofin_node(library_id, media, stem=None):
    folder = kofin_folder_name(library_id, media)
    if stem is None:
        return "library://video/kofin/%s/" % folder
    return "library://video/kofin/%s/%s.xml/" % (folder, stem)


def unwatched_tv_xsp(library_id):
    return (
        "special://profile/playlists/video/Contuary/unwatched_tvshows_%s.xsp"
        % library_id
    )


def studios_node_path(library_id):
    return "library://video/contuary_studios_%s.xml/" % library_id


def studios_node_file(library_id):
    return "contuary_studios_%s.xml" % library_id


def slot_ids(index):
    base = 30000 + 100 * index
    return {
        "group": base,
        "grouplist": base + 1,
        "scrollbar": base + 10,
        "categories": base + 20,
        "inprogress": base + 21,
        "recent": base + 22,
        "unwatched": base + 23,
        "random": base + 24,
        "genres_movies": base + 25,
        "sets": base + 26,
        "genres_shows": base + 24,
        "studios": base + 25,
        "empty": base + 50,
        "prop": "kofin%d" % index,
    }


# (kind, include, header, setting_key, id_key, extras)
_MOVIE_ROWS = (
    (
        "categories",
        "WidgetListCategories",
        "",
        "home_no_movies_categories_widget",
        "categories",
        (),
    ),
    (
        "inprogress",
        "WidgetListPoster",
        "$LOCALIZE[31010]",
        "home_no_movies_inprogress_widget",
        "inprogress",
        (),
    ),
    (
        "recent",
        "WidgetListPoster",
        "$LOCALIZE[20386]",
        "home_no_movies_recentlyadded_widget",
        "recent",
        (),
    ),
    (
        "unwatched",
        "WidgetListPoster",
        "$LOCALIZE[31007]",
        "home_no_movies_unwatched_widget",
        "unwatched",
        (),
    ),
    (
        "random",
        "WidgetListPoster",
        "$LOCALIZE[31006]",
        "home_no_movies_random_widget",
        "random",
        (("browse_mode", "never"),),
    ),
    (
        "genres",
        "WidgetListCategories",
        "$LOCALIZE[135]",
        "home_no_movies_genres_widget",
        "genres_movies",
        (("icon", "$VAR[WidgetGenreIconVar]"), ("icon_height", "70")),
    ),
    (
        "sets",
        "WidgetListPoster",
        "$LOCALIZE[31075]",
        "home_no_movies_sets_widget",
        "sets",
        (
            ("sortby", "random"),
            ("onclick_condition", "true"),
            ("onclick_action", "$VAR[MovieSetOnClickActionVar]"),
        ),
    ),
)

_SHOW_ROWS = (
    (
        "categories",
        "WidgetListCategories",
        "",
        "home_no_tvshows_categories_widget",
        "categories",
        (),
    ),
    (
        "inprogress",
        "WidgetListPoster",
        "$LOCALIZE[626]",
        "home_no_tvshows_inprogress_widget",
        "inprogress",
        (
            ("sortby", "lastplayed"),
            ("sortorder", "descending"),
            ("onclick_condition", "true"),
            ("onclick_action", "$VAR[TVShowOnClickActionVar]"),
        ),
    ),
    (
        "recent",
        "WidgetListEpisodes",
        "$LOCALIZE[20387]",
        "home_no_tvshows_recentlyaddedepisodes_widget",
        "recent",
        (),
    ),
    (
        "unwatched",
        "WidgetListPoster",
        "$LOCALIZE[31122]",
        "home_no_tvshows_unwatched_widget",
        "unwatched",
        (
            ("onclick_condition", "true"),
            ("onclick_action", "$VAR[TVShowOnClickActionVar]"),
        ),
    ),
    (
        "genres",
        "WidgetListCategories",
        "$LOCALIZE[135]",
        "home_no_tvshows_genres_widget",
        "genres_shows",
        (("icon", "$VAR[WidgetGenreIconVar]"), ("icon_height", "70")),
    ),
    (
        "studios",
        "WidgetListCategories",
        "$LOCALIZE[20388]",
        "home_no_tvshows_studios_widget",
        "studios",
        (("icon", "$VAR[WidgetStudioIconVar]"), ("icon_height", "70")),
    ),
)

MOVIE_SETTING_KEYS = tuple(row[3] for row in _MOVIE_ROWS)
SHOW_SETTING_KEYS = tuple(row[3] for row in _SHOW_ROWS)


def _movie_path(kind, mode, library_id):
    if kind == "categories":
        if mode == MODE_SYNCED:
            return kofin_node(library_id, MEDIA_MOVIES)
        return plugin_browse(library_id, MEDIA_MOVIES)
    stems = {
        "inprogress": "inprogress",
        "recent": "recent",
        "unwatched": "unwatched",
        "random": "random",
        "genres": "genres",
        "sets": "sets",
    }
    folder = stems[kind]
    if mode == MODE_SYNCED:
        return kofin_node(library_id, MEDIA_MOVIES, folder)
    return plugin_browse(library_id, MEDIA_MOVIES, folder)


def _show_path(kind, mode, library_id):
    if kind == "categories":
        if mode == MODE_SYNCED:
            return kofin_node(library_id, MEDIA_TVSHOWS)
        return plugin_browse(library_id, MEDIA_TVSHOWS)
    if kind == "unwatched":
        if mode == MODE_SYNCED:
            return unwatched_tv_xsp(library_id)
        return plugin_browse(library_id, MEDIA_TVSHOWS, "unwatched")
    if kind == "studios":
        return studios_node_path(library_id)
    stems = {
        "inprogress": "inprogress",
        "recent": "recentepisodes",
        "genres": "genres",
    }
    folder = stems[kind]
    if mode == MODE_SYNCED:
        return kofin_node(library_id, MEDIA_TVSHOWS, folder)
    return plugin_browse(library_id, MEDIA_TVSHOWS, folder)


def widgets_for(media, mode, library_id, include_studios=False):
    """Widget dicts for one section. Dropped kinds are omitted."""
    if media == MEDIA_MOVIES:
        rows = _MOVIE_ROWS
        path_fn = _movie_path
    elif media == MEDIA_TVSHOWS:
        rows = _SHOW_ROWS
        path_fn = _show_path
    else:
        raise ValueError("unknown media %r" % media)

    out = []
    for kind, include, header, setting_key, id_key, extras in rows:
        if kind == "studios":
            if mode != MODE_SYNCED or not include_studios:
                continue
        if (
            kind == "inprogress"
            and media == MEDIA_TVSHOWS
            and mode == MODE_DYNAMIC
            and DROP_DYNAMIC_TV_INPROGRESS
        ):
            continue
        out.append(
            {
                "kind": kind,
                "include": include,
                "header": header,
                "setting_key": setting_key,
                "id_key": id_key,
                "extras": extras,
                "content_path": path_fn(kind, mode, library_id),
            }
        )
    return out


def all_listing_path(media, mode, library_id):
    if mode == MODE_SYNCED:
        return kofin_node(library_id, media, "all")
    return plugin_browse(library_id, media, "all")


def parse_kofin_folder(name):
    """Return (media, library_id) from a ``kofinmovies…`` / ``kofintvshows…`` name."""
    for media in (MEDIA_MOVIES, MEDIA_TVSHOWS):
        prefix = "kofin%s" % media
        if name.startswith(prefix) and len(name) > len(prefix):
            return media, name[len(prefix) :]
    return None
