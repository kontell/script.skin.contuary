# script.skin.contuary

Helper for the [Contuary](https://github.com/kontell/skin.contuary) skin. It switches the skin's resolution, and it builds one home section per Kofin movie or TV library.

Settings → Skin settings → Resolution opens the selector. The same things from a script:

```
RunScript(script.skin.contuary)
RunScript(script.skin.contuary,2256x1269)
RunScript(script.skin.contuary,_sync)
RunScript(script.skin.contuary,kofinmenu)
```

The selector rewrites the one default `<res>` line in the skin's `addon.xml`. Kodi reads that line when the skin loads, so a resolution change needs a restart. The dialog shows the aspect beside the size. `Skin.String(resolution)` stays the bare name, such as `1920x1200`.

Choices are the 16:9 steps from 1920x1080 to 2400x1350, then the aspects Estuary leaves commented out of `addon.xml`: 4:3, 3:2, 16:10, 17:9, 21:9, 19.5:9 and 18:9.

Generated home sections apply after ReloadSkin.
