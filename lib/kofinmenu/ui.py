"""Dialog manager for generated kofin home sections."""

import os
import shutil

import xbmcgui
import xbmcvfs

from kofinmenu import config, discover
from kofinmenu.generate import (
    save_and_apply,
    skin_supports_kofin_menu,
)
from kofinmenu.paths import MAX_SECTIONS, MODE_DYNAMIC, MODE_SYNCED, STOCK_ICON
from log import notify

_YESNO_NO = getattr(xbmcgui, "DLG_YESNO_NO_BTN", None)


def _dialog():
    return xbmcgui.Dialog()


def _yesno(heading, message):
    kwargs = {}
    if _YESNO_NO is not None:
        kwargs["defaultbutton"] = _YESNO_NO
    return _dialog().yesno(heading, message, **kwargs)


def _reason_tag(reason):
    if reason == "kofin_missing":
        return " [kofin missing]"
    if reason == "kofin_disabled":
        return " [disabled]"
    return ""


def _section_missing(section, libraries, reason):
    if reason != "ok":
        return False
    for row in discover.expand_add_choices(libraries):
        if (
            row["library_id"] == section["library_id"]
            and row["media"] == section["media"]
        ):
            return False
    return True


def _copy_icon(src, section_id):
    ext = os.path.splitext(src)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp"):
        ext = ".png"
    dest_dir = os.path.join(config.addon_data_dir(), "icons")
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    dest = os.path.join(dest_dir, section_id + ext)
    src_path = xbmcvfs.translatePath(src) if src.startswith("special://") else src
    shutil.copy2(src_path, dest)
    return "special://profile/addon_data/script.skin.contuary/icons/%s%s" % (
        section_id,
        ext,
    )


def _pick_library(libraries, doc):
    existing = {(s["library_id"], s["media"]) for s in doc["sections"]}
    choices = []
    for row in discover.expand_add_choices(libraries):
        if (row["library_id"], row["media"]) in existing:
            continue
        tag = "synced" if row.get("synced") else "dynamic"
        choices.append((row, "%s  [%s]  [%s]" % (row["name"], row["media"], tag)))
    if not choices:
        notify("No unused movies or TV libraries.")
        return None
    sel = _dialog().select("Choose a library", [label for _, label in choices])
    if sel < 0:
        return None
    return choices[sel][0]


def _pick_mode(row):
    options = []
    if row.get("synced"):
        options.append((MODE_SYNCED, "Synced (Kodi library)"))
    options.append((MODE_DYNAMIC, "Dynamic (Jellyfin live)"))
    if len(options) == 1:
        return options[0][0]
    sel = _dialog().select(
        "How should this section load?", [label for _, label in options]
    )
    if sel < 0:
        return None
    return options[sel][0]


def _pick_name(library_name):
    if _yesno("Contuary", "Use the Jellyfin name «%s»?" % library_name):
        return library_name, "library"
    typed = _dialog().input("Section name", library_name)
    if not typed:
        return None
    return typed, "custom"


def _pick_icon(media, section_id):
    if _yesno("Contuary", "Use the stock movies/TV icon?"):
        return STOCK_ICON[media], "stock"
    chosen = _dialog().browse(
        2,
        "Choose icon",
        "files",
        ".png|.jpg|.jpeg|.webp",
        True,
        False,
        "special://skin/icons/sidemenu/",
    )
    if not chosen:
        return STOCK_ICON[media], "stock"
    try:
        path = _copy_icon(chosen, section_id)
    except OSError:
        notify("Could not copy that icon; using the stock one.")
        return STOCK_ICON[media], "stock"
    return path, "custom"


def _add_section(doc, libraries):
    if len(doc["sections"]) >= MAX_SECTIONS:
        notify("Already have %d sections." % MAX_SECTIONS)
        return doc
    row = _pick_library(libraries, doc)
    if row is None:
        return doc
    mode = _pick_mode(row)
    if mode is None:
        return doc
    named = _pick_name(row["name"])
    if named is None:
        return doc
    name, name_source = named
    section_id = config.new_section_id()
    icon, icon_source = _pick_icon(row["media"], section_id)
    config.add_section(
        doc,
        {
            "id": section_id,
            "library_id": row["library_id"],
            "media": row["media"],
            "mode": mode,
            "name": name,
            "name_source": name_source,
            "library_name": row["name"],
            "icon": icon,
            "icon_source": icon_source,
            "enabled": True,
        },
    )
    save_and_apply(doc, notify_user=True)
    return doc


def _edit_name(doc, section):
    named = _pick_name(section.get("library_name") or section["name"])
    if named is None:
        return
    section["name"], section["name_source"] = named
    save_and_apply(doc, notify_user=True)


def _edit_icon(doc, section):
    icon, source = _pick_icon(section["media"], section["id"])
    section["icon"] = icon
    section["icon_source"] = source
    save_and_apply(doc, notify_user=True)


def _edit_mode(doc, section, libraries):
    row = {
        "synced": False,
        "media": section["media"],
        "library_id": section["library_id"],
    }
    for candidate in discover.expand_add_choices(libraries):
        if (
            candidate["library_id"] == section["library_id"]
            and candidate["media"] == section["media"]
        ):
            row = candidate
            break
    else:
        row["synced"] = discover.is_synced(section["library_id"], section["media"])
    mode = _pick_mode(row)
    if mode is None:
        return
    section["mode"] = mode
    save_and_apply(doc, notify_user=True)


def _delete_section(doc, section):
    if not _yesno("Contuary", "Delete «%s»?" % section["name"]):
        return doc
    config.remove_section(doc, section["id"])
    save_and_apply(doc, notify_user=True)
    return doc


def _edit_section(doc, section, libraries):
    actions = [
        "Name",
        "Icon",
        "Mode",
        "Move up",
        "Move down",
        "Reset to library name",
        "Delete",
    ]
    sel = _dialog().select(section["name"], actions)
    if sel < 0:
        return
    if sel == 0:
        _edit_name(doc, section)
    elif sel == 1:
        _edit_icon(doc, section)
    elif sel == 2:
        _edit_mode(doc, section, libraries)
    elif sel == 3:
        config.move_section(doc, section["id"], -1)
        save_and_apply(doc, notify_user=True)
    elif sel == 4:
        config.move_section(doc, section["id"], 1)
        save_and_apply(doc, notify_user=True)
    elif sel == 5:
        section["name"] = section.get("library_name") or section["name"]
        section["name_source"] = "library"
        save_and_apply(doc, notify_user=True)
    elif sel == 6:
        _delete_section(doc, section)


def run_manager():
    if not skin_supports_kofin_menu():
        _dialog().ok(
            "Contuary",
            "This Contuary version does not support library sections.",
        )
        return
    try:
        doc = config.load()
    except config.ConfigError as exc:
        notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
        return

    while True:
        reason, libraries = discover.discover_libraries()
        labels = []
        for section in doc["sections"]:
            tag = _reason_tag(reason)
            if _section_missing(section, libraries, reason):
                tag = " [missing]"
            if (
                section["mode"] == MODE_SYNCED
                and reason == "ok"
                and not discover.is_synced(section["library_id"], section["media"])
            ):
                tag += " [not synced]"
            labels.append("%s%s" % (section["name"], tag))
        can_add = reason not in ("kofin_missing", "kofin_disabled")
        if can_add:
            labels.append("Add section...")
        if doc["sections"]:
            labels.append("Clear all...")
        if not labels:
            _dialog().ok(
                "Contuary",
                "No library sections yet, and kofin is not available.",
            )
            return
        sel = _dialog().select("Jellyfin library sections", labels)
        if sel < 0:
            return
        n = len(doc["sections"])
        if can_add and sel == n:
            if reason == "not_logged_in":
                notify("Log in to Kofin first.")
                continue
            if reason == "no_libraries":
                notify("No movies or TV libraries found.")
                continue
            doc = _add_section(doc, libraries)
            continue
        clear_index = n + (1 if can_add else 0)
        if sel == clear_index and doc["sections"]:
            if _yesno("Contuary", "Remove every Jellyfin library section?"):
                doc["sections"] = []
                save_and_apply(doc, notify_user=True)
            continue
        if sel < n:
            _edit_section(doc, doc["sections"][sel], libraries)
