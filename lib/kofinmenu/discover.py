"""Discover kofin movies/tvshows libraries via JSON-RPC. No kofin import."""

from urllib.parse import parse_qs, urlparse

import xbmc

from kofinmenu.paths import MEDIA_MOVIES, MEDIA_TVSHOWS, parse_kofin_folder
from log import log

KOFIN_ID = "plugin.video.kofin"
PLUGIN_ROOT = "plugin://plugin.video.kofin/"
KOFIN_NODES = "library://video/kofin/"

KEEP_TYPES = {MEDIA_MOVIES, MEDIA_TVSHOWS, "mixed"}


def jsonrpc(method, params=None):
    import json

    req = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        req["params"] = params
    raw = xbmc.executeJSONRPC(json.dumps(req))
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": {"message": "invalid json-rpc response"}}


def addon_state():
    data = jsonrpc(
        "Addons.GetAddonDetails",
        {"addonid": KOFIN_ID, "properties": ["enabled"]},
    )
    if data.get("error"):
        return "missing"
    addon = (data.get("result") or {}).get("addon") or {}
    if addon.get("enabled"):
        return "enabled"
    return "disabled"


def _query(file_url):
    parsed = urlparse(file_url or "")
    return {key: values[0] for key, values in parse_qs(parsed.query).items() if values}


def _item_file(item):
    return item.get("file") or item.get("File") or ""


def _item_label(item):
    return item.get("label") or item.get("title") or item.get("Label") or ""


def _listing(directory, media="video"):
    data = jsonrpc(
        "Files.GetDirectory",
        {
            "directory": directory,
            "media": media,
            "properties": ["file", "title", "thumbnail"],
        },
    )
    if data.get("error"):
        return None
    files = (data.get("result") or {}).get("files")
    if files is None:
        return []
    return files


def synced_pairs():
    """Set of (library_id, media) that have a kofin node folder."""
    files = _listing(KOFIN_NODES)
    if files is None:
        return set()
    found = set()
    for item in files:
        file_url = _item_file(item).rstrip("/")
        name = file_url.rsplit("/", 1)[-1]
        if name.endswith(".xml"):
            name = name[: -len(".xml")]
        parsed = parse_kofin_folder(name)
        if parsed:
            found.add((parsed[1], parsed[0]))
    return found


def parse_root_item(item):
    file_url = _item_file(item)
    query = _query(file_url)
    if query.get("mode") != "browse":
        return None
    view = query.get("view") or ""
    media = query.get("type") or ""
    folder = query.get("folder") or ""
    if not view:
        return None
    if media not in KEEP_TYPES:
        if folder == "children" and not media:
            media = "mixed"
        else:
            return None
    if media not in KEEP_TYPES:
        return None
    return {
        "library_id": view,
        "media": media,
        "name": _item_label(item) or view,
        "file": file_url,
    }


def discover_libraries():
    """Return ``(reason, libraries)``.

    reason is ``ok``, ``kofin_missing``, ``kofin_disabled``,
    ``not_logged_in``, or ``no_libraries``.
    """
    state = addon_state()
    if state == "missing":
        log("discover: kofin missing")
        return "kofin_missing", []
    if state == "disabled":
        log("discover: kofin disabled")
        return "kofin_disabled", []

    files = _listing(PLUGIN_ROOT)
    if files is None:
        log("discover: plugin root GetDirectory failed")
        return "no_libraries", []

    rows = []
    settings_only = True
    for item in files:
        query = _query(_item_file(item))
        mode = query.get("mode") or ""
        if mode != "settings":
            settings_only = False
        parsed = parse_root_item(item)
        if parsed:
            rows.append(parsed)

    if settings_only and files:
        log("discover: not logged in (settings-only root)")
        return "not_logged_in", []

    synced = synced_pairs()
    for row in rows:
        if row["media"] == "mixed":
            row["synced"] = (row["library_id"], MEDIA_MOVIES) in synced or (
                row["library_id"],
                MEDIA_TVSHOWS,
            ) in synced
            row["synced_movies"] = (row["library_id"], MEDIA_MOVIES) in synced
            row["synced_tvshows"] = (row["library_id"], MEDIA_TVSHOWS) in synced
        else:
            row["synced"] = (row["library_id"], row["media"]) in synced

    log(
        "discover: %d library row(s), synced folders=%s"
        % (len(rows), sorted("%s/%s" % (mid, media) for mid, media in synced))
    )
    if not rows:
        return "no_libraries", []
    return "ok", rows


def is_synced(library_id, media):
    return (library_id, media) in synced_pairs()


def expand_add_choices(libraries):
    """Flatten mixed rows into movies+tvshows choices for the add dialog."""
    choices = []
    for row in libraries:
        if row["media"] == "mixed":
            for media, synced_key in (
                (MEDIA_MOVIES, "synced_movies"),
                (MEDIA_TVSHOWS, "synced_tvshows"),
            ):
                choices.append(
                    {
                        "library_id": row["library_id"],
                        "media": media,
                        "name": row["name"],
                        "synced": row.get(synced_key, False),
                        "file": row.get("file", ""),
                    }
                )
        else:
            choices.append(row)
    return choices
