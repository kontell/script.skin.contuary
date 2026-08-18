"""Emit Includes_KofinGenerated.xml, Contuary XSPs, and optional studio nodes."""

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcvfs

from kofinmenu import config, discover
from kofinmenu.paths import (
    GENERATOR_VERSION,
    MAX_SECTIONS,
    MEDIA_MOVIES,
    MEDIA_TVSHOWS,
    MODE_SYNCED,
    STOCK_ICON,
    all_listing_path,
    esc_label,
    esc_xml,
    slot_ids,
    studios_node_file,
    widgets_for,
)
from log import log, notify

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
STAMP_PROP = "Contuary.KofinReloaded"
COUNT_STRING = "kofin_menu_count"
SKIN_INCLUDES = "special://home/addons/skin.contuary/xml/Includes.xml"
SKIN_GENERATED = "special://home/addons/skin.contuary/xml/Includes_KofinGenerated.xml"
PROFILE_VIDEO = "special://profile/library/video"
PROFILE_PLAYLISTS = "special://profile/playlists/video/Contuary"
DEBUG_COPY = "special://profile/addon_data/script.skin.contuary/generated"

STUB_BODY = """<?xml version="1.0" encoding="UTF-8"?>
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


def translate(path):
    return xbmcvfs.translatePath(path)


def skin_supports_kofin_menu():
    path = translate(SKIN_INCLUDES)
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return False
    return "Includes_KofinGenerated.xml" in text


def config_hash(doc):
    payload = (
        json.dumps(doc, sort_keys=True, separators=(",", ":"))
        + "|%s" % GENERATOR_VERSION
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def stamp_path():
    return translate(SKIN_GENERATED).rsplit(".", 1)[0] + ".stamp"


def read_stamp():
    try:
        with open(stamp_path(), encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def write_stamp(sig):
    with open(stamp_path(), "w", encoding="utf-8") as fh:
        fh.write(sig + "\n")


def profile_video_exists():
    return os.path.isdir(translate(PROFILE_VIDEO))


def _include_block(name, children, empty_comment):
    if not children:
        return '\t<include name="%s">\n\t\t<!-- %s -->\n\t</include>\n' % (
            name,
            empty_comment,
        )
    return '\t<include name="%s">\n%s\t</include>\n' % (name, "".join(children))


def _widget_xml(widget, list_id):
    lines = [
        '\t\t\t\t<include content="%s" condition="!Skin.HasSetting(%s)">\n'
        % (widget["include"], widget["setting_key"]),
        '\t\t\t\t\t<param name="content_path" value="%s"/>\n'
        % esc_xml(widget["content_path"]),
        '\t\t\t\t\t<param name="widget_header" value="%s"/>\n' % widget["header"],
        '\t\t\t\t\t<param name="widget_target" value="videos"/>\n',
        '\t\t\t\t\t<param name="list_id" value="%d"/>\n' % list_id,
    ]
    for key, value in widget["extras"]:
        lines.append('\t\t\t\t\t<param name="%s" value="%s"/>\n' % (key, value))
    lines.append("\t\t\t\t</include>\n")
    return "".join(lines)


def _empty_condition(widgets, ids):
    parts_on = []
    parts_empty = []
    for widget in widgets:
        key = widget["setting_key"]
        list_id = ids[widget["id_key"]]
        parts_on.append("!Skin.HasSetting(%s)" % key)
        parts_empty.append(
            "[Skin.HasSetting(%s) | [Integer.IsEqual(Container(%d).NumItems,0)"
            " + !Container(%d).IsUpdating]]" % (key, list_id, list_id)
        )
    if not parts_on:
        return "false"
    # OR binds looser than AND in skin boolean expressions. Without the
    # brackets, "!A | !B + emptyA + emptyB" is true whenever A is on.
    return "[" + " | ".join(parts_on) + "] + " + " + ".join(parts_empty)


def _section_xml(section, index, include_studios):
    ids = slot_ids(index)
    media = section["media"]
    mode = section["mode"]
    library_id = section["library_id"]
    widgets = widgets_for(media, mode, library_id, include_studios=include_studios)
    prop = ids["prop"]
    name = esc_label(section["name"])
    chunks = [
        '\t\t<control type="group" id="%d">\n' % ids["group"],
        "\t\t\t<visible>String.IsEqual(Container(9000).ListItem.Property(id),%s)</visible>\n"
        % prop,
        '\t\t\t<include content="Visible_Right_Delayed">\n',
        '\t\t\t\t<param name="id" value="%s"/>\n' % prop,
        "\t\t\t</include>\n",
        '\t\t\t<control type="grouplist" id="%d">\n' % ids["grouplist"],
        "\t\t\t\t<include>WidgetGroupListCommon</include>\n",
        "\t\t\t\t<pagecontrol>%d</pagecontrol>\n" % ids["scrollbar"],
        '\t\t\t\t<include content="MainMenuTitle">\n',
        '\t\t\t\t\t<param name="label" value="%s"/>\n' % name,
        "\t\t\t\t</include>\n",
    ]
    for widget in widgets:
        chunks.append(_widget_xml(widget, ids[widget["id_key"]]))
    chunks.append("\t\t\t</control>\n")
    chunks.append('\t\t\t<include content="ImageWidget">\n')
    chunks.append('\t\t\t\t<param name="text_label" value="$LOCALIZE[31179]"/>\n')
    chunks.append('\t\t\t\t<param name="button_label" value="$LOCALIZE[186]"/>\n')
    chunks.append('\t\t\t\t<param name="button_onclick" value="SetFocus(9000)"/>\n')
    chunks.append('\t\t\t\t<param name="button_id" value="%d"/>\n' % ids["empty"])
    chunks.append('\t\t\t\t<param name="visible_2" value="false"/>\n')
    chunks.append(
        '\t\t\t\t<param name="visible" value="%s"/>\n' % _empty_condition(widgets, ids)
    )
    chunks.append("\t\t\t</include>\n")
    chunks.append(
        '\t\t\t<include content="WidgetScrollbar" condition="Skin.HasSetting(touchmode)">\n'
    )
    chunks.append(
        '\t\t\t\t<param name="scrollbar_id" value="%d"/>\n' % ids["scrollbar"]
    )
    chunks.append("\t\t\t</include>\n")
    chunks.append("\t\t</control>\n")
    return "".join(chunks)


def _menu_item_xml(section, index):
    ids = slot_ids(index)
    listing = all_listing_path(section["media"], section["mode"], section["library_id"])
    icon = section.get("icon") or STOCK_ICON[section["media"]]
    if section.get("icon_source") == "custom" and not os.path.isfile(
        translate(icon) if icon.startswith("special://") else icon
    ):
        icon = STOCK_ICON[section["media"]]
    return (
        "\t\t<item>\n"
        "\t\t\t<label>%s</label>\n"
        "\t\t\t<onclick>ActivateWindow(Videos,%s,return)</onclick>\n"
        '\t\t\t<property name="menu_id">$NUMBER[%d]</property>\n'
        "\t\t\t<thumb>%s</thumb>\n"
        '\t\t\t<property name="id">%s</property>\n'
        "\t\t</item>\n"
        % (
            esc_label(section["name"]),
            esc_xml(listing),
            ids["group"],
            esc_xml(icon),
            ids["prop"],
        )
    )


def render_includes(doc):
    sections = config.enabled_sections(doc)[:MAX_SECTIONS]
    include_studios = profile_video_exists()
    section_xml = []
    movie_items = []
    show_items = []
    for index, section in enumerate(sections):
        section_xml.append(_section_xml(section, index, include_studios))
        item = _menu_item_xml(section, index)
        if section["media"] == MEDIA_MOVIES:
            movie_items.append(item)
        else:
            show_items.append(item)
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<includes>\n"
        + _include_block(
            "KofinGeneratedSections", section_xml, "stub: no generated sections"
        )
        + _include_block(
            "KofinGeneratedMovieMenuItems",
            movie_items,
            "stub: no generated movie items",
        )
        + _include_block(
            "KofinGeneratedShowMenuItems",
            show_items,
            "stub: no generated show items",
        )
        + "</includes>\n"
    )
    return body


def parse_check(text):
    ET.fromstring(COMMENT.sub("", text))


def write_generated_xml(text):
    dest = translate(SKIN_GENERATED)
    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        raise OSError("skin xml dir missing: %s" % parent)
    tmp = dest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    try:
        parse_check(text)
    except ET.ParseError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    os.replace(tmp, dest)
    debug_dir = translate(DEBUG_COPY)
    try:
        if not os.path.isdir(debug_dir):
            os.makedirs(debug_dir)
        with open(
            os.path.join(debug_dir, "Includes_KofinGenerated.xml"),
            "w",
            encoding="utf-8",
        ) as fh:
            fh.write(text)
    except OSError as exc:
        log("debug copy skipped: %s" % exc)
    return dest


def _write_unwatched_xsp(section):
    library_id = section["library_id"]
    name = esc_xml(section.get("library_name") or section["name"])
    dest_dir = translate(PROFILE_PLAYLISTS)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    dest = os.path.join(dest_dir, "unwatched_tvshows_%s.xsp" % library_id)
    body = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
        '<smartplaylist type="tvshows">\n'
        "    <name>Unwatched — %s</name>\n"
        "    <match>all</match>\n"
        '    <rule field="tag" operator="is"><value>%s</value></rule>\n'
        '    <rule field="numwatched" operator="is"><value>0</value></rule>\n'
        '    <rule field="numepisodes" operator="greaterthan"><value>0</value></rule>\n'
        "    <limit>15</limit>\n"
        '    <order direction="ascending">random</order>\n'
        "</smartplaylist>\n" % (name, name)
    )
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(body)
    return dest


def _write_studios_node(section):
    video_dir = translate(PROFILE_VIDEO)
    if not os.path.isdir(video_dir):
        return None
    library_id = section["library_id"]
    name = esc_xml(section.get("library_name") or section["name"])
    dest = os.path.join(video_dir, studios_node_file(library_id))
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<node order="0" type="filter">\n'
        "    <label>20388</label>\n"
        "    <icon>DefaultStudios.png</icon>\n"
        "    <content>tvshows</content>\n"
        "    <group>studios</group>\n"
        "    <match>all</match>\n"
        '    <rule field="tag" operator="is"><value>%s</value></rule>\n'
        "</node>\n" % name
    )
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(body)
    return dest


def _cleanup_orphans(keep_ids):
    playlists = translate(PROFILE_PLAYLISTS)
    if os.path.isdir(playlists):
        for name in os.listdir(playlists):
            if not name.startswith("unwatched_tvshows_") or not name.endswith(".xsp"):
                continue
            lib_id = name[len("unwatched_tvshows_") : -len(".xsp")]
            if lib_id not in keep_ids:
                try:
                    os.remove(os.path.join(playlists, name))
                except OSError:
                    pass
    video_dir = translate(PROFILE_VIDEO)
    if os.path.isdir(video_dir):
        for name in os.listdir(video_dir):
            if not name.startswith("contuary_studios_") or not name.endswith(".xml"):
                continue
            lib_id = name[len("contuary_studios_") : -len(".xml")]
            if lib_id not in keep_ids:
                try:
                    os.remove(os.path.join(video_dir, name))
                except OSError:
                    pass


def write_profile_artifacts(doc):
    keep = set()
    for section in config.enabled_sections(doc):
        if section["media"] == MEDIA_TVSHOWS and section["mode"] == MODE_SYNCED:
            keep.add(section["library_id"])
            _write_unwatched_xsp(section)
            _write_studios_node(section)
    _cleanup_orphans(keep)


def refresh_library_names(doc):
    reason, libraries = discover.discover_libraries()
    if reason != "ok":
        return False
    by_pair = {}
    for row in discover.expand_add_choices(libraries):
        by_pair[(row["library_id"], row["media"])] = row["name"]
    changed = False
    for section in doc.get("sections", []):
        if section.get("name_source") != "library":
            continue
        name = by_pair.get((section["library_id"], section["media"]))
        if name and (section["name"] != name or section.get("library_name") != name):
            section["name"] = name
            section["library_name"] = name
            changed = True
    return changed


def set_count_string(doc):
    count = len(config.enabled_sections(doc))
    xbmc.executebuiltin("Skin.SetString(%s,%s)" % (COUNT_STRING, count))


def generate(doc):
    """Write profile artifacts and, if the skin has the hook, the include file."""
    config.validate(doc)
    write_profile_artifacts(doc)
    text = render_includes(doc)
    parse_check(text)
    dest = None
    if skin_supports_kofin_menu():
        dest = write_generated_xml(text)
        write_stamp(config_hash(doc))
        log("generate: %d section(s) -> %s" % (len(config.enabled_sections(doc)), dest))
    else:
        log("generate: skin has no Includes_KofinGenerated.xml hook; json only")
    set_count_string(doc)
    return dest


def reload_skin():
    xbmc.executebuiltin("ReloadSkin()")


def apply(doc, reload=True, notify_user=False):
    try:
        generate(doc)
    except OSError as exc:
        log("generate write failed: %s" % exc, xbmc.LOGERROR)
        notify(
            "Cannot update the home menu (skin folder is not writable)",
            xbmcgui.NOTIFICATION_ERROR,
        )
        return False
    except ET.ParseError as exc:
        log("generate parse failed, kept previous file: %s" % exc, xbmc.LOGERROR)
        notify("Could not update the home menu", xbmcgui.NOTIFICATION_ERROR)
        return False
    except config.ConfigError as exc:
        log("generate config error: %s" % exc, xbmc.LOGERROR)
        notify(str(exc), xbmcgui.NOTIFICATION_ERROR)
        return False
    if reload:
        reload_skin()
    if notify_user:
        notify("Home menu updated.")
    return True


def save_and_apply(doc, reload=True, notify_user=False):
    config.save(doc)
    return apply(doc, reload=reload, notify_user=notify_user)


def ensure():
    """Home onload: rebuild from JSON if the stamp/hash is stale."""
    if not skin_supports_kofin_menu():
        log("ensure: skin does not support kofin menu", xbmc.LOGDEBUG)
        return
    try:
        doc = config.load()
    except config.ConfigError as exc:
        log("ensure: bad config: %s" % exc, xbmc.LOGERROR)
        return
    if refresh_library_names(doc):
        try:
            config.save(doc)
        except OSError as exc:
            log("ensure: could not save refreshed names: %s" % exc)
    sig = config_hash(doc)
    win = xbmcgui.Window(10000)
    if win.getProperty(STAMP_PROP) == sig:
        return
    if read_stamp() == sig and os.path.isfile(translate(SKIN_GENERATED)):
        return
    win.setProperty(STAMP_PROP, sig)
    log("ensure: stamp mismatch, regenerating")
    apply(doc, reload=True, notify_user=False)
