#!/usr/bin/env python3
"""Map factory for The Atlas.

Generates a new five-edition map page from a JSON config, using ruston/ as the
canonical template: panel copy, camera, contour intervals and the hypsometric
ramp (both derived from the real DEM), landmark set, live-conditions config,
optional trail extraction, thumbnails, and the home-page card.

Usage:
  python3 tools/mapfactory.py config.json            # writes <slug>/ + assets + home card
  python3 tools/mapfactory.py config.json --out DIR  # write the page elsewhere (dry run)
  python3 tools/mapfactory.py config.json --skip-thumbs --skip-home

See tools/README.md and tools/example-config.json.
"""
import json, math, re, sys, os, io, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- DEM helpers ----------------
def fetch_dem(lat_n, lat_s, lon_w, lon_e, z):
    import numpy as np
    from PIL import Image
    n = 2 ** z
    def xy(lat, lon):
        return ((lon + 180) / 360 * n,
                (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    fx0, fy0 = xy(lat_n, lon_w); fx1, fy1 = xy(lat_s, lon_e)
    tx0, ty0, tx1, ty1 = int(fx0), int(fy0), int(fx1), int(fy1)
    dem = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256))
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{tx}/{ty}.png"
            im = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=20).read())).convert("RGB")
            a = np.asarray(im, dtype=np.float64)
            dem[(ty-ty0)*256:(ty-ty0+1)*256, (tx-tx0)*256:(tx-tx0+1)*256] = \
                a[:,:,0]*256 + a[:,:,1] + a[:,:,2]/256 - 32768
    px0, py0 = int((fx0-tx0)*256), int((fy0-ty0)*256)
    px1, py1 = int((fx1-tx0)*256), int((fy1-ty0)*256)
    return dem[py0:py1, px0:px1]

RELIEF_COLORS = ['#2e6f7f','#3a8068','#69a06c','#a3b974','#cdc384','#cfa868','#bd8454','#a8714a']

def derive_terrain(cfg):
    """Elevation stats -> contour thresholds, hypsometric ramp, legend labels."""
    import numpy as np
    b = cfg['bbox']  # [w, s, e, n]
    z = 11 if (b[2]-b[0]) > 0.25 else 12
    dem = fetch_dem(b[3], b[1], b[0], b[2], z)
    lo, hi = float(np.percentile(dem, 2)), float(np.percentile(dem, 98))
    relief_ft = (hi - lo) * 3.28084
    if relief_ft < 500:
        thr = "{ 9:[200,1000], 11:[100,500], 12:[40,200], 14:[20,100], 16:[10,50] }"
        thr_dense = "{ 9:[100,500], 11:[40,200], 12:[20,100], 14:[10,50], 16:[5,20] }"
    elif relief_ft < 2500:
        thr = "{ 9:[500,1000], 10:[200,1000], 12:[100,500], 13:[40,200], 15:[20,100] }"
        thr_dense = "{ 9:[200,1000], 10:[100,500], 12:[40,200], 13:[20,100], 15:[10,50] }"
    else:
        thr = "{ 8:[1000,5000], 10:[500,1000], 12:[200,1000], 14:[100,500] }"
        thr_dense = "{ 8:[500,1000], 10:[200,1000], 12:[100,500], 14:[40,200] }"
    n = len(RELIEF_COLORS)
    stops = []
    for i, c in enumerate(RELIEF_COLORS):
        stops.append(f"{round(lo + (hi-lo)*i/(n-1))},'{c}'")
    ramp = "[" + ", ".join(stops) + "]"
    return dict(lo_ft=int(lo*3.28084), hi_ft=int(hi*3.28084), dem=dem,
                thr=thr, thr_dense=thr_dense, ramp=ramp,
                exag=2.5 if relief_ft < 500 else (1.8 if relief_ft < 2500 else 1.3))

# ---------------- page generation ----------------
def rx(s, pattern, repl, count=1, flags=re.S, label=''):
    new, n = re.subn(pattern, repl, s, count=count, flags=flags)
    if n != count:
        raise SystemExit(f"factory anchor failed: {label or pattern[:60]} (matched {n}, wanted {count})")
    return new

def esc(t):  # for use inside re.sub replacement strings
    return t.replace('\\', r'\\')

def landmark_js(cfg):
    out = ["  var LANDMARKS = ["]
    items = []
    for lm in cfg['landmarks']:
        blurb = lm['blurb'].replace("'", "\\u2019")
        items.append(
            "    { name:'%s', short:'%s', cat:'%s', tier:%d, lngLat:[%s, %s], zoom:%s,\n"
            "      blurb:'%s' }" % (
                lm['name'].replace("'", "\\u2019"), lm['short'].replace("'", "\\u2019"),
                lm['cat'], lm.get('tier', 2), lm['lngLat'][0], lm['lngLat'][1],
                lm.get('zoom', 15), blurb))
    out.append(",\n".join(items))
    out.append("  ];")
    return "\n".join(out)

def build(cfg, outdir, skip_thumbs, skip_home):
    tpl = open(os.path.join(ROOT, 'ruston', 'index.html')).read()
    s = tpl
    slug, name = cfg['slug'], cfg['name']
    base = 'https://sulleyneal.github.io/Maps/'
    t = derive_terrain(cfg)
    b = cfg['bbox']
    pad_w, pad_h = (b[2]-b[0]) * 0.6, (b[3]-b[1]) * 0.6

    s = rx(s, r'<title>.*?</title>', f'<title>{esc(cfg["title"])}</title>', label='title')
    s = rx(s, r'<meta name="description" content=".*?">',
           f'<meta name="description" content="{esc(cfg["desc"])}">', label='meta desc')
    s = rx(s, r'<meta property="og:title" content=".*?">',
           f'<meta property="og:title" content="{esc(cfg["title"])}">', label='og title')
    s = rx(s, r'<meta property="og:description" content=".*?">',
           f'<meta property="og:description" content="{esc(cfg["desc"])}">', label='og desc')
    s = rx(s, r'<meta property="og:image" content=".*?">',
           f'<meta property="og:image" content="{base}assets/{slug}-relief.jpg">', label='og image')
    s = rx(s, r'<meta property="og:url" content=".*?">',
           f'<meta property="og:url" content="{base}{slug}/">', label='og url')

    s = rx(s, r'<div class="t1">.*?</div>\n  <div class="t2">.*?</div>',
           f'<div class="t1">{esc(cfg["cartouche"][0])}</div>\n  <div class="t2">{esc(cfg["cartouche"][1])}</div>',
           label='cartouche')
    s = rx(s, r'<p class="eyebrow">.*?</p>', f'<p class="eyebrow">{esc(cfg["eyebrow"])}</p>', label='eyebrow')
    s = rx(s, r'<h1>RUSTON</h1>', f'<h1>{esc(name.upper())}</h1>', label='h1')
    s = rx(s, r'<p class="tagline">.*?</p>', f'<p class="tagline">{esc(cfg["tagline"])}</p>', label='tagline')
    s = rx(s, r'<p class="about">.*?</p>\n    <p class="about"[^>]*>.*?</p>',
           '<p class="about">%s</p>\n    <p class="about" style="font-size:13.5px">%s</p>' %
           (esc(cfg['about'][0]), esc(cfg['about'][1])), label='about')
    facts = "\n".join(f'      <div><b>{k}</b>{v}</div>' for k, v in cfg['facts'])
    s = rx(s, r'<div class="facts">.*?</div>\n\n', f'<div class="facts">\n{esc(facts)}\n    </div>\n\n', label='facts')
    s = rx(s, r'(<h2>The Lay of the Land</h2>\n)    <p class="small">.*?</p>',
           r'\1    <p class="small">' + esc(cfg['terrainNote']) + '</p>', label='lay of land')
    s = rx(s, r'<div class="elev-lab">.*?</div>',
           '<div class="elev-lab"><span>&approx;%s ft <i>low</i></span><span>&approx;%s ft <i>high</i></span></div>'
           % (f"{t['lo_ft']:,}", f"{t['hi_ft']:,}"), label='elev labels')
    if cfg.get('extraSections'):
        s = rx(s, r'(    <h2>The Lay of the Land</h2>)', esc(cfg['extraSections']) + r'\n\1', label='extra sections')
    s = rx(s, r'<div id="veil">.*?</div>', f'<div id="veil">{esc(cfg.get("veil", "Surveying the country&hellip;"))}</div>',
           label='veil')

    cam = cfg['camera']
    s = rx(s, r'var HOME = isNarrow\n.*?\n.*?;\n',
           "var HOME = isNarrow\n"
           f"    ? {{ center:[{cam['center'][0]}, {cam['center'][1]}], zoom:{cam['zoom']-0.7}, pitch:45, bearing:0 }}\n"
           f"    : {{ center:[{cam['center'][0]}, {cam['center'][1]}], zoom:{cam['zoom']}, pitch:{cam.get('pitch',52)}, bearing:{cam.get('bearing',-8)} }};\n",
           label='HOME')
    s = rx(s, r'maxBounds:\[\[.*?\]\],',
           f'maxBounds:[[{round(b[0]-pad_w,2)},{round(b[1]-pad_h,2)}],[{round(b[2]+pad_w,2)},{round(b[3]+pad_h,2)}]],',
           label='maxBounds')
    s = rx(s, r'var EXAGGERATION = [\d.]+;', f'var EXAGGERATION = {t["exag"]};', label='exaggeration')
    s = rx(s, r'thresholds: \{[^}]*\},\n    contourLayer', f'thresholds: {t["thr"]},\n    contourLayer',
           count=2, label='thresholds')
    # the second occurrence is the dense source; redo it precisely
    parts = s.split(f'thresholds: {t["thr"]},\n    contourLayer')
    if len(parts) == 3:
        s = parts[0] + f'thresholds: {t["thr"]},\n    contourLayer' + parts[1] + \
            f'thresholds: {t["thr_dense"]},\n    contourLayer' + parts[2]
    s = rx(s, r'var RELIEF_STOPS = \[.*?\];', f'var RELIEF_STOPS = {t["ramp"]};', label='relief stops')

    regions = ",\n".join(
        "    { type:'Feature', geometry:{ type:'Point', coordinates:[%s, %s] },\n"
        "      properties:{ t:'%s' } }" % (r['lngLat'][0], r['lngLat'][1], r['text'])
        for r in cfg.get('regionLabels', []))
    if regions:
        s = rx(s, r'var regionGeo = \{ type:\'FeatureCollection\', features:\[.*?\n  \] \};',
               'var regionGeo = { type:\'FeatureCollection\', features:[\n' + esc(regions) + '\n  ] };',
               label='regions')

    cats = cfg['cats']  # {key: {label, antique, midnight}}
    cl = ", ".join(f"{k}:'{v['label']}'" for k, v in cats.items())
    s = rx(s, r'var CAT_LABELS = \{.*?\};', 'var CAT_LABELS = { ' + cl + ' };', label='cat labels')
    pal_a = ", ".join(f"{k}:'{v['antique']}'" for k, v in cats.items())
    pal_m = ", ".join(f"{k}:'{v['midnight']}'" for k, v in cats.items())
    occ = re.findall(r'cats:\{ [^}]*\}', s)
    if len(occ) != 2:
        raise SystemExit('factory anchor failed: palette cats')
    s = s.replace(occ[0], 'cats:{ ' + pal_a + ' }', 1)
    s = s.replace(occ[1], 'cats:{ ' + pal_m + ' }', 1)

    i0 = s.index('  var LANDMARKS = [')
    i1 = s.index('  ];', i0) + len('  ];')
    s = s[:i0] + landmark_js(cfg) + s[i1:]

    cond = cfg.get('conditions', {})
    cond_js = "  var CONDITIONS = " + json.dumps(
        {k: v for k, v in cond.items()} or
        {"lat": cam['center'][1], "lon": cam['center'][0], "tz": "America/Chicago"}) + ";"
    s = rx(s, r'  var CONDITIONS = \{.*?\};', esc(cond_js), label='conditions')

    s = s.replace("'ruston-theme'", f"'{slug}-theme'").replace("'ruston-prefs'", f"'{slug}-prefs'")

    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'index.html'), 'w').write(s)
    if not os.path.exists(os.path.join(outdir, 'trails.js')):
        open(os.path.join(outdir, 'trails.js'), 'w').write('window.TRAILS = {"trails":[]};\n')
    print(f"page: {outdir}/index.html  ({t['lo_ft']}-{t['hi_ft']} ft, exag {t['exag']})")

    if not skip_thumbs:
        import importlib.util
        spec = importlib.util.spec_from_file_location('thumbs', os.path.join(ROOT, 'tools', 'thumbs.py'))
        th = importlib.util.module_from_spec(spec); spec.loader.exec_module(th)
        th.render_all(t['dem'], slug, os.path.join(ROOT, 'assets'),
                      [c for c in RELIEF_COLORS])
    if not skip_home:
        h = open(os.path.join(ROOT, 'index.html')).read()
        card = ("    ,{\n"
                f"      slug:'{slug}',\n"
                f"      title:'{name}',\n"
                f"      region:'{cfg['region']}',\n"
                f"      desc:'{cfg['cardDesc']}',\n"
                f"      tags:{json.dumps(cfg.get('tags', []))},\n"
                f"      added:'{cfg.get('added', '2026')}'\n"
                "    }\n    /* mapfactory:insert */")
        assert '/* mapfactory:insert */' in h
        h = h.replace('    /* mapfactory:insert */', card, 1)
        open(os.path.join(ROOT, 'index.html'), 'w').write(h)
        print("home card: added")

if __name__ == '__main__':
    args = sys.argv[1:]
    cfgp = args[0]
    cfg = json.load(open(cfgp))
    out = os.path.join(ROOT, cfg['slug'])
    if '--out' in args: out = args[args.index('--out') + 1]
    build(cfg, out, '--skip-thumbs' in args, '--skip-home' in args or '--out' in args)
