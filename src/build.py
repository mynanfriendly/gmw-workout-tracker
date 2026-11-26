"""Builds GMW Workout Tracker (repo root) and MK Workouts (/mk) from src/app.html."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SRC = os.path.join(os.path.dirname(__file__), 'src', 'app.html')
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/gmw-workout-tracker'
FONT = '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'

APPS = [
    dict(dir='', cache='gmw-v2', icon=dict(text='GMW', c1=(138, 31, 47), c2=(84, 14, 28), fg=(226, 189, 85), shadow=(40, 6, 14)),
         cfg=dict(app='gmw', brand='GMW', sub='Workout Tracker', title='Workout Tracker', key='gmw-tracker-v1', file='GMW', accent='blue', gym=None),
         bg='#0b0d12'),
    dict(dir='mk', cache='mk-v1', icon=dict(text='MK', c1=(31, 107, 255), c2=(0, 183, 255), fg=(255, 255, 255), shadow=(10, 30, 90)),
         cfg=dict(app='mk', brand='MK', sub='Workouts', title='MK Workouts', key='mk-workouts-v1', file='MK', accent='blue', gym='Watford'),
         bg='#0b0d12'),
]

def icon(size, text, c1, c2, fg, shadow):
    S = size * 4
    xs = np.linspace(0, 1, S)
    g = xs[None, :] * 0.6 + xs[:, None] * 0.4
    arr = np.zeros((S, S, 3), dtype=np.uint8)
    for i in range(3):
        arr[..., i] = (c1[i] + (c2[i] - c1[i]) * g).astype(np.uint8)
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, int(S * (0.36 if len(text) > 2 else 0.44)))
    bb = d.textbbox((0, 0), text, font=f)
    x = (S - (bb[2] - bb[0])) / 2 - bb[0]
    y = (S - (bb[3] - bb[1])) / 2 - bb[1] - S * 0.02
    d.text((x + S * 0.012, y + S * 0.018), text, font=f, fill=shadow)
    d.text((x, y), text, font=f, fill=fg)
    d.rounded_rectangle([S * 0.24, S * 0.70, S * 0.76, S * 0.735], radius=S * 0.02, fill=fg)
    return img.resize((size, size), Image.LANCZOS)

SW = """const CACHE = '%s';
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-192.png', './icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES.map(f => new Request(f, {cache: 'reload'})))));
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
// Serve from the phone first (works with no signal), refresh in the background when online.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.match(e.request, {ignoreSearch: true}).then(hit => {
    const net = fetch(e.request).then(res => {
      if (res && res.ok && new URL(e.request.url).origin === location.origin) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); }
      return res;
    }).catch(() => hit);
    return hit || net;
  }));
});
"""

src = open(SRC, encoding='utf-8').read()
for a in APPS:
    out = os.path.join(OUT, a['dir'])
    os.makedirs(out, exist_ok=True)
    c = a['cfg']
    html = src.replace('{{CFG}}', json.dumps(c)).replace('{{TITLE}}', c['title'])
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(out, 'sw.js'), 'w').write(SW % a['cache'])
    man = dict(name=c['title'], short_name=c['title'], description=f"{c['title']} – log sets, reps, weight and seat height",
               start_url='./', scope='./', display='standalone', orientation='portrait', background_color=a['bg'], theme_color=a['bg'],
               icons=[dict(src='icon-192.png', sizes='192x192', type='image/png'), dict(src='icon-512.png', sizes='512x512', type='image/png'),
                      dict(src='icon-512.png', sizes='512x512', type='image/png', purpose='maskable')])
    open(os.path.join(out, 'manifest.webmanifest'), 'w').write(json.dumps(man, indent=2))
    for s in (180, 192, 512):
        icon(s, **a['icon']).save(os.path.join(out, f'icon-{s}.png'))
    print('built', out or '/')
