"""Shared log / toast helpers. Prefix matches the existing resolution script."""

import xbmc
import xbmcgui


def log(msg, level=None):
    if level is None:
        level = xbmc.LOGINFO
    xbmc.log("[script.skin.contuary] " + msg, level)


def notify(message, icon=None):
    if icon is None:
        icon = xbmcgui.NOTIFICATION_INFO
    xbmcgui.Dialog().notification("Contuary", message, icon, 5000)
