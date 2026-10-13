"""The resolution table covers Estuary's commented aspects, and applying one
writes that aspect into the single default <res> line."""

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<addon id="skin.contuary" version="2.8.0">
\t<extension point="xbmc.gui.skin">
\t\t<res width="1920" height="1080" aspect="16:9" default="true" folder="xml" />
\t</extension>
</addon>
"""

# The aspects Estuary ships commented out, in that comment's order.
ESTUARY_ASPECTS = [
    ("1920x1440", 1920, 1440, "4:3"),
    ("1920x1280", 1920, 1280, "3:2"),
    ("1920x1200", 1920, 1200, "16:10"),
    ("2040x1080", 2040, 1080, "17:9"),
    ("2560x1080", 2560, 1080, "21:9"),
    ("2338x1080", 2338, 1080, "19.5:9"),
    ("2160x1080", 2160, 1080, "18:9"),
]


def test_estuary_aspects_follow_the_16_9_ladder():
    from resolution import OPTIONS

    by_name = {opt["name"]: opt for opt in OPTIONS}
    names = [opt["name"] for opt in OPTIONS]
    ladder_end = names.index("2400x1350")
    estuary_names = [row[0] for row in ESTUARY_ASPECTS]
    assert names[ladder_end + 1 :] == estuary_names
    for name, width, height, aspect in ESTUARY_ASPECTS:
        opt = by_name[name]
        assert (opt["width"], opt["height"], opt["aspect"]) == (width, height, aspect)


def test_skin_string_stays_the_bare_name():
    from resolution import label_for

    assert label_for((1920, 1080)) == "1920x1080"
    assert label_for((1920, 1200)) == "1920x1200"
    assert label_for((2560, 1080)) == "2560x1080"


def test_select_label_shows_the_aspect(kodi_fs, monkeypatch):
    import resolution

    seen = {}

    class FakeDialog:
        def select(self, heading, labels, preselect=-1):
            seen["heading"] = heading
            seen["labels"] = labels
            seen["preselect"] = preselect
            return -1

    monkeypatch.setattr(resolution.xbmcgui, "Dialog", FakeDialog)
    assert resolution._select_option((1920, 1080)) is None
    assert seen["labels"][0] == "1920x1080 (16:9)  [current]"
    assert seen["preselect"] == 0
    assert "1920x1200 (16:10)" in seen["labels"]
    assert "2560x1080 (21:9)" in seen["labels"]


def test_apply_writes_the_chosen_aspect(kodi_fs):
    from resolution import OPTIONS, _apply, _read_addon_xml

    path = kodi_fs["home"] / "addons" / "skin.contuary" / "addon.xml"
    path.write_text(SAMPLE, encoding="utf-8")
    target = next(opt for opt in OPTIONS if opt["name"] == "2338x1080")
    assert _apply(target, _read_addon_xml())
    written = path.read_text(encoding="utf-8")
    assert written.count('default="true"') == 1
    assert (
        '<res width="2338" height="1080" aspect="19.5:9" '
        'default="true" folder="xml" />'
    ) in written


def _run(kodi_fs, monkeypatch, arg, sample=SAMPLE):
    """Run the resolution path over ``sample``; the builtins it issued, and
    the dialogs it raised."""
    import resolution

    path = kodi_fs["home"] / "addons" / "skin.contuary" / "addon.xml"
    path.write_text(sample, encoding="utf-8")
    builtins, asked = [], []
    monkeypatch.setattr(
        resolution.xbmc,
        "executebuiltin",
        lambda command, wait=False: builtins.append((command, wait)),
    )

    class Dialog:
        def notification(self, _heading, message, *_args):
            asked.append(("notification", message))

        def yesno(self, *_args, **_kwargs):
            asked.append(("yesno",))
            return False

    monkeypatch.setattr(resolution.xbmcgui, "Dialog", Dialog)
    resolution.run(arg)
    return builtins, asked, path.read_text(encoding="utf-8")


def test_a_change_takes_effect_by_a_rescan_and_a_reload_not_a_restart(
    kodi_fs, monkeypatch
):
    """Kodi sizes a skin from the add-on manager's copy of addon.xml, so the
    manager reads the file again before the skin is reloaded, and the scan
    is waited for. Nobody is asked to quit Kodi."""
    builtins, asked, written = _run(kodi_fs, monkeypatch, "2256x1269")

    assert 'width="2256" height="1269"' in written
    assert builtins == [
        ("Skin.SetString(resolution,1920x1080)", False),
        ("Skin.SetString(resolution,2256x1269)", False),
        ("UpdateLocalAddons()", True),
        ("ReloadSkin()", False),
    ]
    assert asked == []


def test_nothing_is_reloaded_when_nothing_was_written(kodi_fs, monkeypatch):
    # Already at that size.
    builtins, asked, written = _run(kodi_fs, monkeypatch, "1920x1080")
    assert written == SAMPLE
    assert [command for command, _ in builtins] == [
        "Skin.SetString(resolution,1920x1080)"
    ]
    assert asked == [("notification", "Already at 1920x1080")]
    # A name the table does not have.
    builtins, _, written = _run(kodi_fs, monkeypatch, "640x480")
    assert written == SAMPLE and not any("Reload" in c for c, _ in builtins)
    # No active line to rewrite.
    broken = SAMPLE.replace('default="true"', 'default="false"')
    builtins, _, written = _run(kodi_fs, monkeypatch, "2256x1269", broken)
    assert written == broken
    assert not any("Reload" in c or "UpdateLocal" in c for c, _ in builtins)


def test_a_sync_never_reloads(kodi_fs, monkeypatch):
    builtins, asked, written = _run(kodi_fs, monkeypatch, "_sync")
    assert written == SAMPLE and asked == []
    assert builtins == [("Skin.SetString(resolution,1920x1080)", False)]
