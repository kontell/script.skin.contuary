"""Headless argv helpers used by live tests."""

import xbmcgui

from kofinmenu import config, discover
from kofinmenu.generate import save_and_apply
from kofinmenu.paths import (
    MEDIA_MOVIES,
    MEDIA_TVSHOWS,
    MODE_DYNAMIC,
    MODE_SYNCED,
    STOCK_ICON,
)
from log import notify


def _library_name(library_id, media):
    reason, libraries = discover.discover_libraries()
    if reason == "ok":
        for row in discover.expand_add_choices(libraries):
            if row["library_id"] == library_id and row["media"] == media:
                return row["name"]
    return library_id


def add_section(library_id, media, mode, name=None):
    if media not in (MEDIA_MOVIES, MEDIA_TVSHOWS):
        raise config.ConfigError("media must be movies or tvshows")
    if mode not in (MODE_SYNCED, MODE_DYNAMIC):
        raise config.ConfigError("mode must be synced or dynamic")
    doc = config.load()
    library_name = _library_name(library_id, media)
    display = name or library_name
    config.add_section(
        doc,
        {
            "library_id": library_id,
            "media": media,
            "mode": mode,
            "name": display,
            "name_source": "custom" if name else "library",
            "library_name": library_name,
            "icon": STOCK_ICON[media],
            "icon_source": "stock",
            "enabled": True,
        },
    )
    save_and_apply(doc)
    return doc


def remove_section(section_id):
    doc = config.load()
    config.remove_section(doc, section_id)
    save_and_apply(doc)
    return doc


def clear_sections():
    doc = config.empty_doc()
    save_and_apply(doc)
    return doc


def set_section(section_id, field, value):
    doc = config.load()
    config.set_field(doc, section_id, field, value)
    save_and_apply(doc)
    return doc


def handle_error(exc):
    notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
