"""Switch the active <res> in skin.contuary's addon.xml.

Usage (via Kodi):
  RunScript(script.skin.contuary)         — show selector dialog
  RunScript(script.skin.contuary,<name>)  — apply the named option directly
  RunScript(script.skin.contuary,_sync)   — silently sync Skin.String(resolution)

Kodi parses <res> at skin load, so a Kodi restart is required for the
new resolution to take effect.
"""

import re
import sys

import xbmc
import xbmcgui
import xbmcvfs

OPTIONS = [
    {"name": "1920x1080", "width": 1920, "height": 1080, "aspect": "16:9"},
    {"name": "1968x1107", "width": 1968, "height": 1107, "aspect": "16:9"},
    {"name": "2016x1134", "width": 2016, "height": 1134, "aspect": "16:9"},
    {"name": "2048x1152", "width": 2048, "height": 1152, "aspect": "16:9"},
    {"name": "2064x1161", "width": 2064, "height": 1161, "aspect": "16:9"},
    {"name": "2112x1188", "width": 2112, "height": 1188, "aspect": "16:9"},
    {"name": "2160x1215", "width": 2160, "height": 1215, "aspect": "16:9"},
    {"name": "2208x1242", "width": 2208, "height": 1242, "aspect": "16:9"},
    {"name": "2256x1269", "width": 2256, "height": 1269, "aspect": "16:9"},
    {"name": "2304x1296", "width": 2304, "height": 1296, "aspect": "16:9"},
    {"name": "2352x1323", "width": 2352, "height": 1323, "aspect": "16:9"},
    {"name": "2400x1350", "width": 2400, "height": 1350, "aspect": "16:9"},
]

SKIN_ID = "skin.contuary"
SKIN_STRING = "resolution"

_DEFAULT_RES_RE = re.compile(
    r'<res\s+width="(?P<w>\d+)"\s+height="(?P<h>\d+)"'
    r'\s+aspect="(?P<a>[^"]+)"\s+default="true"\s+folder="xml"\s*/>'
)


def _log(msg, level=xbmc.LOGINFO):
    xbmc.log("[script.skin.contuary] " + msg, level)


def _notify(message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification("Contuary", message, icon, 5000)


def _addon_xml_path():
    return xbmcvfs.translatePath("special://home/addons/%s/addon.xml" % SKIN_ID)


def _read_addon_xml():
    try:
        with open(_addon_xml_path(), "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        _log("read failed: %s" % exc, xbmc.LOGERROR)
        return None


def _write_addon_xml(xml):
    try:
        with open(_addon_xml_path(), "w", encoding="utf-8") as fh:
            fh.write(xml)
        return True
    except OSError as exc:
        _log("write failed: %s" % exc, xbmc.LOGERROR)
        return False


def _current(xml):
    m = _DEFAULT_RES_RE.search(xml)
    if not m:
        return None
    return (int(m.group("w")), int(m.group("h")))


def _label_for(current):
    if current is None:
        return ""
    for opt in OPTIONS:
        if (opt["width"], opt["height"]) == current:
            return opt["name"]
    return "%dx%d" % current


def _sync_skin_string(current):
    label = _label_for(current)
    xbmc.executebuiltin("Skin.SetString(%s,%s)" % (SKIN_STRING, label))


def _select_option(current):
    labels = []
    preselect = -1
    for i, opt in enumerate(OPTIONS):
        label = opt["name"]
        if current and (opt["width"], opt["height"]) == current:
            label += "  [current]"
            preselect = i
        labels.append(label)
    sel = xbmcgui.Dialog().select("Contuary Resolution", labels, preselect=preselect)
    if sel < 0:
        return None
    return OPTIONS[sel]


def _apply(target, xml):
    new_line = (
        '<res width="%d" height="%d" aspect="%s" '
        'default="true" folder="xml" />'
        % (target["width"], target["height"], target["aspect"])
    )
    new_xml, n = _DEFAULT_RES_RE.subn(new_line, xml, count=1)
    if n == 0:
        _log("active <res> line not found", xbmc.LOGERROR)
        _notify("Active <res> line not found in addon.xml", xbmcgui.NOTIFICATION_ERROR)
        return False
    if not _write_addon_xml(new_xml):
        _notify("Could not write skin addon.xml", xbmcgui.NOTIFICATION_ERROR)
        return False
    _log("set default <res> to %s" % target["name"])
    xbmc.executebuiltin("Skin.SetString(%s,%s)" % (SKIN_STRING, target["name"]))
    return True


def main():
    arg = sys.argv[1].strip() if len(sys.argv) >= 2 and sys.argv[1].strip() else None

    xml = _read_addon_xml()
    if xml is None:
        _notify("Could not read skin addon.xml", xbmcgui.NOTIFICATION_ERROR)
        return

    current = _current(xml)
    _sync_skin_string(current)

    if arg == "_sync":
        return

    if arg is None:
        target = _select_option(current)
        if target is None:
            return
    else:
        target = next(
            (o for o in OPTIONS if o["name"].lower() == arg.lower()),
            None,
        )
        if target is None:
            names = ", ".join(o["name"] for o in OPTIONS)
            _notify("Unknown option (try: %s)" % names, xbmcgui.NOTIFICATION_ERROR)
            return

    if current == (target["width"], target["height"]):
        _notify("Already at %s" % target["name"])
        return

    if not _apply(target, xml):
        return

    if xbmcgui.Dialog().yesno(
        "Contuary",
        "Resolution set to %s.\n\nKodi must restart for the change to "
        "take effect. Quit Kodi now?" % target["name"],
    ):
        xbmc.executebuiltin("Quit")
    else:
        _notify("Restart Kodi to apply %s" % target["name"])


if __name__ == "__main__":
    main()
