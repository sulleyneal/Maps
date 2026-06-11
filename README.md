# A Living Chart of Ruston, Louisiana

An interactive, antique-styled terrain map of Ruston and Lincoln Parish, Louisiana —
parchment tones, raised 3-D relief, contour lines, hatched railroads, and a set of
annotated landmarks, drawn entirely from live, publicly available data.

## Viewing

Open `index.html` in any modern browser (an internet connection is required for the
map data). No build step, no API keys, no accounts.

```sh
# or serve it locally:
python3 -m http.server 8000   # then visit http://localhost:8000
```

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
