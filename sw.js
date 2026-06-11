/* The Atlas service worker — offline support for the charts. */
var VERSION = 'atlas-v1';
var SHELL = 'shell-' + VERSION;
var TILES = 'atlas-tiles';          /* shared with in-page "save this area" */
var DATA = 'atlas-data';

var SHELL_URLS = [
  './', 'ruston/', 'broken-bow/',
  'ruston/trails.js', 'broken-bow/trails.js',
  'vendor/maplibre-gl.js', 'vendor/maplibre-gl.css', 'vendor/maplibre-contour.min.js',
  'manifest.webmanifest'
];

var TILE_HOSTS = ['tiles.openfreemap.org', 's3.amazonaws.com',
                  'fonts.googleapis.com', 'fonts.gstatic.com'];
var LIVE_HOSTS = ['waterservices.usgs.gov', 'api.open-meteo.com'];
var TILE_CAP = 4000;

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(SHELL).then(function(c){
      return Promise.all(SHELL_URLS.map(function(u){
        return c.add(u).catch(function(){});
      }));
    }).then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(k){
        if (k.indexOf('shell-') === 0 && k !== SHELL) return caches.delete(k);
      }));
    }).then(function(){ return self.clients.claim(); })
  );
});

function trimTiles(){
  caches.open(TILES).then(function(c){
    c.keys().then(function(keys){
      if (keys.length > TILE_CAP) {
        var n = keys.length - TILE_CAP;
        for (var i = 0; i < n; i++) c.delete(keys[i]);
      }
    });
  });
}

self.addEventListener('fetch', function(e){
  var url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;

  /* documents & same-origin shell: network-first so updates land, cache for offline */
  if (url.origin === location.origin) {
    e.respondWith(
      fetch(e.request).then(function(r){
        var copy = r.clone();
        caches.open(SHELL).then(function(c){ c.put(e.request, copy); });
        return r;
      }).catch(function(){
        return caches.match(e.request, { ignoreSearch: true }).then(function(m){
          return m || caches.match('./');
        });
      })
    );
    return;
  }

  /* live data: network-first, stale fallback */
  if (LIVE_HOSTS.indexOf(url.hostname) !== -1) {
    e.respondWith(
      fetch(e.request).then(function(r){
        var copy = r.clone();
        caches.open(DATA).then(function(c){ c.put(e.request, copy); });
        return r;
      }).catch(function(){ return caches.match(e.request); })
    );
    return;
  }

  /* tiles, glyphs, fonts: cache-first */
  if (TILE_HOSTS.indexOf(url.hostname) !== -1) {
    e.respondWith(
      caches.match(e.request).then(function(m){
        if (m) return m;
        return fetch(e.request).then(function(r){
          if (r && (r.ok || r.type === 'opaque')) {
            var copy = r.clone();
            caches.open(TILES).then(function(c){ c.put(e.request, copy); trimTiles(); });
          }
          return r;
        });
      })
    );
  }
});
