"""Load / save / validate kofin_sections.json."""

import json
import os
import uuid

import xbmcvfs

from kofinmenu.paths import (
    MAX_SECTIONS,
    MEDIA_MOVIES,
    MEDIA_TVSHOWS,
    MODE_DYNAMIC,
    MODE_SYNCED,
    STOCK_ICON,
)

SCHEMA_VERSION = 1
CONFIG_NAME = "kofin_sections.json"
ADDON_DATA = "special://profile/addon_data/script.skin.contuary"

MEDIA_VALUES = (MEDIA_MOVIES, MEDIA_TVSHOWS)
MODE_VALUES = (MODE_SYNCED, MODE_DYNAMIC)
NAME_SOURCES = ("library", "custom")
ICON_SOURCES = ("stock", "custom")


class ConfigError(Exception):
    pass


def addon_data_dir():
    return xbmcvfs.translatePath(ADDON_DATA)


def config_path():
    return os.path.join(addon_data_dir(), CONFIG_NAME)


def empty_doc():
    return {"version": SCHEMA_VERSION, "sections": []}


def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def load():
    path = config_path()
    if not os.path.isfile(path):
        return empty_doc()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ConfigError("could not read config: %s" % exc)
    return validate(doc)


def save(doc):
    validate(doc)
    _ensure_dir(addon_data_dir())
    path = config_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)
    return path


def new_section_id():
    return uuid.uuid4().hex[:8]


def _require(section, key):
    if key not in section or section[key] in (None, ""):
        raise ConfigError("section missing %s" % key)
    return section[key]


def validate(doc):
    if not isinstance(doc, dict):
        raise ConfigError("config root must be an object")
    version = doc.get("version", SCHEMA_VERSION)
    if not isinstance(version, int):
        raise ConfigError("version must be an int")
    if version > SCHEMA_VERSION:
        raise ConfigError("config version %s is newer than this script" % version)
    sections = doc.get("sections")
    if not isinstance(sections, list):
        raise ConfigError("sections must be a list")
    if len(sections) > MAX_SECTIONS:
        raise ConfigError("more than %d sections" % MAX_SECTIONS)
    seen_ids = set()
    seen_libs = set()
    for section in sections:
        if not isinstance(section, dict):
            raise ConfigError("section must be an object")
        sid = _require(section, "id")
        if sid in seen_ids:
            raise ConfigError("duplicate section id %s" % sid)
        seen_ids.add(sid)
        media = _require(section, "media")
        if media not in MEDIA_VALUES:
            raise ConfigError("bad media %r" % media)
        mode = _require(section, "mode")
        if mode not in MODE_VALUES:
            raise ConfigError("bad mode %r" % mode)
        library_id = _require(section, "library_id")
        pair = (library_id, media)
        if pair in seen_libs:
            raise ConfigError("duplicate library %s/%s" % pair)
        seen_libs.add(pair)
        _require(section, "name")
        if section.get("name_source", "library") not in NAME_SOURCES:
            raise ConfigError("bad name_source")
        if section.get("icon_source", "stock") not in ICON_SOURCES:
            raise ConfigError("bad icon_source")
        section.setdefault("name_source", "library")
        section.setdefault("library_name", section["name"])
        section.setdefault("icon", STOCK_ICON[media])
        section.setdefault("icon_source", "stock")
        section.setdefault("enabled", True)
    doc["version"] = SCHEMA_VERSION
    doc["sections"] = sections
    return doc


def enabled_sections(doc):
    return [s for s in doc.get("sections", []) if s.get("enabled", True)]


def find_section(doc, section_id):
    for section in doc.get("sections", []):
        if section["id"] == section_id:
            return section
    return None


def add_section(doc, section):
    validate(doc)
    if len(doc["sections"]) >= MAX_SECTIONS:
        raise ConfigError("already have %d sections" % MAX_SECTIONS)
    if "id" not in section or not section["id"]:
        section["id"] = new_section_id()
    pair = (section["library_id"], section["media"])
    for existing in doc["sections"]:
        if (existing["library_id"], existing["media"]) == pair:
            raise ConfigError("that library is already a section")
        if existing["id"] == section["id"]:
            section["id"] = new_section_id()
    section.setdefault("name_source", "library")
    section.setdefault("library_name", section.get("name", ""))
    section.setdefault("icon", STOCK_ICON[section["media"]])
    section.setdefault("icon_source", "stock")
    section.setdefault("enabled", True)
    doc["sections"].append(section)
    return validate(doc)


def remove_section(doc, section_id):
    before = len(doc.get("sections", []))
    doc["sections"] = [s for s in doc.get("sections", []) if s["id"] != section_id]
    if len(doc["sections"]) == before:
        raise ConfigError("no section %s" % section_id)
    return validate(doc)


def set_field(doc, section_id, field, value):
    section = find_section(doc, section_id)
    if section is None:
        raise ConfigError("no section %s" % section_id)
    allowed = {
        "name",
        "icon",
        "mode",
        "name_source",
        "icon_source",
        "library_name",
        "enabled",
    }
    if field not in allowed:
        raise ConfigError("cannot set %s" % field)
    if field == "mode" and value not in MODE_VALUES:
        raise ConfigError("bad mode %r" % value)
    section[field] = value
    if field == "name":
        section["name_source"] = "custom"
    if field == "icon":
        section["icon_source"] = "custom"
    return validate(doc)


def move_section(doc, section_id, delta):
    sections = doc.get("sections", [])
    index = next((i for i, s in enumerate(sections) if s["id"] == section_id), -1)
    if index < 0:
        raise ConfigError("no section %s" % section_id)
    dest = index + delta
    if dest < 0 or dest >= len(sections):
        return doc
    sections[index], sections[dest] = sections[dest], sections[index]
    return validate(doc)
