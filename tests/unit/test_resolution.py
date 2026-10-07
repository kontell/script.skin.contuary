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
