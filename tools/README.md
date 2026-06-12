# Map factory

Generates a new five-edition map for the atlas from a JSON config, using
`ruston/index.html` as the canonical template. The factory handles the
mechanical 80%: page copy, camera, contour intervals and hypsometric ramp
(derived from the real DEM for the region), category palette, landmarks,
live-conditions wiring, thumbnails for all five editions, and the home-page
card.

```sh
# dry run (writes the page to /tmp, doesn't touch the home page):
python3 tools/mapfactory.py tools/example-config.json --out /tmp/test-map --skip-thumbs

# the real thing:
python3 tools/mapfactory.py my-town.json
git add -A && git commit && git push   # the Pages workflow deploys it
```

Requires `pip install pillow numpy` and network access to the AWS terrain
tiles. See `tools/example-config.json` for every field.

## What stays manual (and matters)

- **Landmark accuracy.** Verify every coordinate before it goes in the
  config. The Overture Maps places dataset is the best source — query it
  with pyarrow against `s3://overturemaps-us-west-2/release/<latest>/theme=places/`
  filtered to your bbox, and search the names you care about. This is how
  every landmark in the existing maps was placed.
- **Trails.** If the region has named OSM trails, extract them with the same
  Overture approach (`theme=transportation/type=segment`, class path/footway/
  track, stitch by name, sample the DEM for profiles) and write the result to
  `<slug>/trails.js` in the format the pages expect (see an existing
  trails.js). Without it the factory writes an empty stub and the Trails
  section hides itself.
- **The prose.** The about paragraphs, blurbs and seasonal notes are the
  soul of these maps. Write them like you'd tell a friend.
- **River/lake gauges.** If the region has a USGS gauge worth watching, add
  `river`/`lake` blocks to `conditions` (see broken-bow/index.html for the
  shape).
