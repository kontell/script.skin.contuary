"""Contuary skin helper: resolution switcher and kofin home-menu generator.

Usage (via Kodi):
  RunScript(script.skin.contuary)              — resolution selector
  RunScript(script.skin.contuary,<name>)       — apply a named resolution
  RunScript(script.skin.contuary,_sync)        — sync Skin.String(resolution)
  RunScript(script.skin.contuary,kofinmenu)    — manage Jellyfin library sections
  RunScript(script.skin.contuary,_ensure)      — rebuild generated home XML if stale

Headless (live tests):
  _kofin_add,<library_id>,movies|tvshows,synced|dynamic[,name]
  _kofin_remove,<section_id>
  _kofin_clear
  _kofin_set,<section_id>,name|icon|mode,<value>
"""

import os
import sys

_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from kofinmenu import actions, config  # noqa: E402
from kofinmenu.generate import ensure  # noqa: E402
from kofinmenu.ui import run_manager  # noqa: E402
from log import notify  # noqa: E402
from resolution import run as run_resolution  # noqa: E402


def _arg(index):
    if len(sys.argv) <= index:
        return None
    value = sys.argv[index].strip()
    return value or None


def main():
    arg = _arg(1)

    if arg == "_ensure":
        ensure()
        return
    if arg == "kofinmenu":
        run_manager()
        return
    if arg == "_kofin_add":
        library_id = _arg(2)
        media = _arg(3)
        mode = _arg(4)
        name = _arg(5)
        if not library_id or not media or not mode:
            notify("Usage: _kofin_add,<id>,movies|tvshows,synced|dynamic[,name]")
            return
        try:
            actions.add_section(library_id, media, mode, name)
        except config.ConfigError as exc:
            actions.handle_error(exc)
        return
    if arg == "_kofin_remove":
        section_id = _arg(2)
        if not section_id:
            notify("Usage: _kofin_remove,<section_id>")
            return
        try:
            actions.remove_section(section_id)
        except config.ConfigError as exc:
            actions.handle_error(exc)
        return
    if arg == "_kofin_clear":
        try:
            actions.clear_sections()
        except config.ConfigError as exc:
            actions.handle_error(exc)
        return
    if arg == "_kofin_set":
        section_id = _arg(2)
        field = _arg(3)
        value = _arg(4)
        if not section_id or not field or value is None:
            notify("Usage: _kofin_set,<section_id>,name|icon|mode,<value>")
            return
        try:
            actions.set_section(section_id, field, value)
        except config.ConfigError as exc:
            actions.handle_error(exc)
        return

    run_resolution(arg)


if __name__ == "__main__":
    main()
