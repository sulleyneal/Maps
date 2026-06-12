"""Thumbnail renders for the atlas home page (all five editions) from a DEM array."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def hillshade(dem, exag=3.0, az=335, alt=45):
    dy, dx = np.gradient(dem * exag)
    slope = np.pi/2 - np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, dy)
    azr, altr = math.radians(360-az+90), math.radians(alt)
    return np.clip(np.sin(altr)*np.sin(slope) + np.cos(altr)*np.cos(slope)*np.cos(azr-aspect), 0, 1)

def hex2rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))

def smooth(d, passes=2):
    k = np.array([0.054, 0.244, 0.404, 0.244, 0.054])
    d = d.astype(np.float64)
    for _ in range(passes):
        d = np.apply_along_axis(lambda r: np.convolve(r, k, mode='same'), 1, d)
        d = np.apply_along_axis(lambda c: np.convolve(c, k, mode='same'), 0, d)
    return d

def _vignette(img, alpha):
    size = img.size
    v = Image.new("L", size, 0)
    d = ImageDraw.Draw(v)
    d.rectangle([0, 0, size[0], size[1]], fill=alpha)
    d.ellipse([-size[0]*0.25, -size[1]*0.25, size[0]*1.25, size[1]*1.25], fill=0)
    return Image.composite(Image.new("RGB", size, (0, 0, 0)), img,
                           v.filter(ImageFilter.GaussianBlur(60)))

def tinted(dem, ramp, shade, size):
    lo, hi = np.percentile(dem, 2), np.percentile(dem, 98)
    t = np.clip((dem-lo)/(hi-lo+1e-9), 0, 1)
    stops = [hex2rgb(c) for c in ramp]
    idx = t*(len(stops)-1)
    i0 = np.clip(idx.astype(int), 0, len(stops)-2)
    f = idx-i0
    arr = np.zeros(dem.shape+(3,))
    for c in range(3):
        sv = np.array([st[c] for st in stops], dtype=np.float64)
        arr[:, :, c] = sv[i0]*(1-f) + sv[i0+1]*f
    arr = arr*(shade[0] + shade[1]*hillshade(dem)[:, :, None])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize(size, Image.LANCZOS)

def topo(dem, size):
    d = smooth(dem, 3)
    lo, hi = np.percentile(d, 2), np.percentile(d, 98)
    iv = max(2, round((hi-lo)/14))
    c = np.floor(d/iv)
    edge = (np.diff(c, axis=0, prepend=c[:1]) != 0) | (np.diff(c, axis=1, prepend=c[:, :1]) != 0)
    c5 = np.floor(d/(iv*5))
    edge5 = (np.diff(c5, axis=0, prepend=c5[:1]) != 0) | (np.diff(c5, axis=1, prepend=c5[:, :1]) != 0)
    arr = np.tile(np.array(hex2rgb('#f4f1e8'), dtype=np.float64), d.shape+(1,)).reshape(d.shape+(3,))
    arr[edge] = np.array(hex2rgb('#94794a'), dtype=np.float64)
    arr[edge5] = np.array(hex2rgb('#5e492a'), dtype=np.float64)
    return Image.fromarray(arr.astype(np.uint8)).resize(size, Image.LANCZOS)

def hydro(dem, size):
    d = smooth(dem, 2)
    H, W = d.shape
    pad = np.pad(d, 1, mode='edge')
    shifts = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    dist = np.array([math.sqrt(abs(a)+abs(b)) for a, b in shifts])
    drops = np.stack([(d - pad[1+dy:1+dy+H, 1+dx:1+dx+W])/dist[k]
                      for k, (dy, dx) in enumerate(shifts)])
    best = np.argmax(drops, axis=0)
    ok = (np.max(drops, axis=0) > 0).ravel()
    dy = np.array([s[0] for s in shifts]); dx = np.array([s[1] for s in shifts])
    tgt = np.clip((np.arange(H)[:, None]+dy[best])*W + (np.arange(W)[None, :]+dx[best]),
                  0, H*W-1).ravel()
    acc = np.ones(H*W)
    for i in np.argsort(d, axis=None)[::-1]:
        if ok[i]: acc[tgt[i]] += acc[i]
    v = np.log1p(acc.reshape(H, W))
    th = np.percentile(v, 97.2)
    mask = np.clip((v-th)/(v.max()-th+1e-9), 0, 1)**0.6
    arr = np.tile(np.array(hex2rgb('#070a10'), dtype=np.float64), d.shape+(1,)).reshape(d.shape+(3,))
    arr = arr*(0.7+0.5*hillshade(d, exag=2)[:, :, None])
    lo_c = np.array(hex2rgb('#155a8a')); hi_c = np.array(hex2rgb('#7fd8ff'))
    line = lo_c[None, None, :]*(1-mask[:, :, None]) + hi_c[None, None, :]*mask[:, :, None]
    arr = np.where(mask[:, :, None] > 0.02, np.maximum(arr, line*mask[:, :, None]**0.5), arr)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    glow = img.filter(ImageFilter.GaussianBlur(2))
    img = Image.blend(img, Image.fromarray(np.maximum(np.asarray(img), np.asarray(glow))), 0.6)
    return img.resize(size, Image.LANCZOS)

ANTIQUE = ['#a9bfae', '#ded8b2', '#e9dcb2', '#dcbf92', '#c69a72']
MIDNIGHT = ['#142936', '#1a3328', '#37452a', '#5d5132', '#84684a']

def render_all(dem, slug, assets_dir, relief_ramp, size=(680, 440)):
    jobs = {
        'antique':  lambda: _vignette(tinted(dem, ANTIQUE, (0.55, 0.65), size), 45),
        'midnight': lambda: _vignette(tinted(dem, MIDNIGHT, (0.35, 0.95), size), 70),
        'relief':   lambda: _vignette(tinted(dem, relief_ramp, (0.55, 0.6), size), 45),
        'topo':     lambda: _vignette(topo(dem, size), 36),
        'hydro':    lambda: _vignette(hydro(dem, size), 70),
    }
    for theme, fn in jobs.items():
        out = f"{assets_dir}/{slug}-{theme}.jpg"
        fn().convert('RGB').save(out, quality=82, optimize=True)
        print("thumb:", out)
