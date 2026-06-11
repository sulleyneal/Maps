# The Atlas

A small collection of interactive, antique-styled maps drawn from live, publicly
available data. Each map lives in its own directory; `index.html` at the root is the home page —
a themed gallery with terrain thumbnails (in `assets/`), where every chart opens
in either the antique or midnight edition. To add a map, add an entry to the
`MAPS` list in the home page and drop two thumbnails in `assets/`.

| Map | Path |
|---|---|
| **Ruston, Louisiana** — one page, two switchable editions: an antique parchment chart and a modern "Midnight" dark map. 3-D relief, contours, hatched railroads, and 20 verified landmarks across the piney hills of Lincoln Parish. Open with `?theme=antique` or `?theme=midnight`; switch live in the map. | [`ruston/`](ruston/) |
| **Broken Bow & Beavers Bend, Oklahoma** — same two-edition chart for the Broken Bow Lake country: Beavers Bend State Park, Hochatown, hiking trails (Boren network, Skyline, Friends), offroad country in the Ouachita National Forest, trout water below the dam, and 26 verified points of interest. | [`broken-bow/`](broken-bow/) |

## Viewing

Open `index.html` (or `ruston/index.html`) in any modern browser — an internet
connection is required for the map data, but there is no build step, no API keys,
and no accounts. With GitHub Pages enabled, the atlas is served at
`https://sulleyneal.github.io/Maps/` and the Ruston chart at
`https://sulleyneal.github.io/Maps/ruston/`.

```sh
# or serve it locally:
python3 -m http.server 8000   # then visit http://localhost:8000
```

## The Ruston chart

- **Drag** to pan, **scroll** to zoom, **right-drag** (or two fingers) to tilt and rotate
- Click the **compass rose** to face north again
- Click a **landmark tag** on the map, or an entry in the panel, for its story
- Toggles in the panel switch the 3-D terrain, contour lines, and landmark tags
- Point at the map to read the ground elevation; the view is shareable via the URL hash

## How it's made

| Ingredient | Source |
|---|---|
| Streets, water, rail, names | [OpenStreetMap](https://www.openstreetmap.org/copyright) vector tiles served by [OpenFreeMap](https://openfreemap.org) (no key, no limits) |
| Elevation (3-D terrain, hillshade) | [Terrain Tiles on AWS](https://registry.opendata.aws/terrain-tiles/) — USGS 3DEP / SRTM, Mapzen terrarium encoding |
| Contour lines | Generated in the browser from the same DEM by [maplibre-contour](https://github.com/onthegomap/maplibre-contour) |
| Rendering | [MapLibre GL JS](https://maplibre.org) with a hand-written vintage style (vendored in `vendor/`) |
| Typefaces | EB Garamond & IM Fell English via Google Fonts |

The cartographic style is an original MapLibre style sheet written for this chart —
buff paper, iron-gall ink, antique road reds, and teal water — inspired by
19th-century county survey maps. Terrain relief is exaggerated 2.5× (the piney
hills are real, but gentle: roughly 130–360 ft across the parish, verified against
the USGS elevation tiles).

Map data © OpenStreetMap contributors (ODbL). Elevation data courtesy USGS and NASA.
