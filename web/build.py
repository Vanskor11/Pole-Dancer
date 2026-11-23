# Builds the Vercel site from PoleClearance.html (the one file you keep editing).
# Run:  python web/build.py      then deploy the web/public folder.
import hashlib, json, os, shutil

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '..', 'PoleClearance.html'), encoding='utf-8').read()
out = os.path.join(here, 'public')
os.makedirs(out, exist_ok=True)

head = '''<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#1e40af">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon-192.png">
</head>'''
# offline support: the service worker keeps a copy so the app opens with no signal
tail = '''<script>
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('/sw.js').catch(() => {});
</script>
</body>'''
assert src.count('</head>') == 1 and src.count('</body>') == 1
html = src.replace('</head>', head, 1).replace('</body>', tail, 1)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8', newline='').write(html)

for f in ('icon.svg', 'icon-192.png', 'icon-512.png'):
    if os.path.exists(os.path.join(here, f)): shutil.copy(os.path.join(here, f), out)

json.dump({
    'name': 'Erotic Pole Dancer Tool', 'short_name': 'Pole Tool',
    'start_url': '/', 'scope': '/', 'display': 'standalone',
    'background_color': '#0f172a', 'theme_color': '#1e40af',
    'icons': [
        {'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        {'src': '/icon.svg', 'sizes': 'any', 'type': 'image/svg+xml'},
    ],
}, open(os.path.join(out, 'manifest.webmanifest'), 'w'), indent=2)

# cache name changes with every build, so a new deploy replaces the offline copy
ver = hashlib.sha1(html.encode()).hexdigest()[:10]
open(os.path.join(out, 'sw.js'), 'w', newline='').write(f'''const CACHE = 'pole-{ver}';
const CORE = ['/', '/manifest.webmanifest', '/icon.svg', '/icon-192.png', '/icon-512.png'];
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE))); self.skipWaiting(); }});
self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
}});
// pages: network first (always get the newest version), cached copy when offline
// everything else (icons, fonts): cache first, saved as it is used
self.addEventListener('fetch', e => {{
  const r = e.request; if (r.method !== 'GET') return;
  if (r.mode === 'navigate') {{
    e.respondWith(fetch(r).then(res => {{ const c = res.clone(); caches.open(CACHE).then(x => x.put('/', c)); return res; }})
      .catch(() => caches.match('/')));
    return;
  }}
  e.respondWith(caches.match(r).then(hit => hit || fetch(r).then(res => {{
    if (res.ok || res.type === 'opaque') {{ const c = res.clone(); caches.open(CACHE).then(x => x.put(r, c)); }}
    return res;
  }})));
}});
''')

print('built', out, ver)
