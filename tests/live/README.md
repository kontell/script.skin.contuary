# LibreELEC live matrix — kofin home sections

Drive the Piers box with kodi-drive. Do not invent a host. Never `cat`
`~/.config/kodi-drive/targets.env`.

```sh
kodi-discover
kodi-remote get Application.GetProperties '{"properties":["version","name"]}'
```

Settle: nav 800 ms, dialogs 1500 ms, ReloadSkin / new nodes 8 s.
New `strings.po` ids need a **Kodi restart**, not ReloadSkin.

Headless setup:

```sh
kodi-builtin 'RunScript(script.skin.contuary,_kofin_clear)'
kodi-builtin 'RunScript(script.skin.contuary,_kofin_add,<id>,movies,synced)'
kodi-builtin 'RunScript(script.skin.contuary,_kofin_add,<id>,movies,dynamic,Kids)'
```

Evidence goes in `tests/live/results/kofin-menu/` (gitignored). Each cell
needs a `notes.md` that **enumerates** cards and says pass/fail, plus
`listing.json` from `Files.GetDirectory` on every widget path.

Comparison standard is in the design doc: kinds/order, include types,
scoped titles (not categories), read screenshots, 9000 nav.

| # | Cell |
| --- | --- |
| 0 | Baseline stock Movies / Shows |
| 1 | 1 movies, synced |
| 2 | 1 movies, dynamic |
| 3 | 1 shows, synced |
| 4 | 1 shows, dynamic |
| 5 | 2 movies (bleed test) |
| 6 | Custom name |
| 7 | Custom icon |
| 8 | Stock name + icon |
| 9 | kofin disabled; button 628 still deletes |
| 10 | Missing library (fake id) |
| 11 | Empty library (fake id) |
| 12 | ReloadSkin |
| 13 | Stub overwrite → `_ensure` restores |
| 14 | Stock still matches baseline |
| 15 | `home_no_movies_genres_widget` hides both |
| 16 | Nav including empty section |
| 17 | Log: no parse errors, no `Skin has invalid include` |
