"""Сборка игры из index.html:
  CarQuiz.html   — один файл со встроенными логотипами (можно просто скинуть на телефон)
  docs/          — сайт для GitHub Pages: тот же файл + manifest + service worker,
                   после первого открытия работает без интернета и ставится на экран «Домой».
Запуск:  python build.py
"""
import base64, hashlib, json, pathlib, re

root = pathlib.Path(__file__).parent
src = (root / "index.html").read_text(encoding="utf-8")

logos = {}
for f in sorted((root / "logos-small").glob("*.png")):
    logos[f.stem] = "data:image/png;base64," + base64.b64encode(f.read_bytes()).decode()

pattern = r"const IMG = slug => `[^`]*`;"
assert re.search(pattern, src), "строка с IMG не найдена"
replacement = "const LOGOS = " + json.dumps(logos) + ";\nconst IMG = slug => LOGOS[slug];"
offline = re.sub(pattern, lambda m: replacement, src, count=1)

(root / "CarQuiz.html").write_text(offline, encoding="utf-8")

# ---------- сайт для GitHub Pages ----------
docs = root / "docs"
docs.mkdir(exist_ok=True)

head = """<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-180.png">
<meta name="theme-color" content="#f5f6f8">
<meta name="apple-mobile-web-app-title" content="Угадай марку">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="mobile-web-app-capable" content="yes">
</head>"""
register = """<script>
if ("serviceWorker" in navigator && location.protocol.indexOf("http") === 0) {
  navigator.serviceWorker.register("sw.js").catch(function () {});
}
</script>
</body>"""
site = offline.replace("</head>", head, 1).replace("</body>", register, 1)
(docs / "index.html").write_text(site, encoding="utf-8")

manifest = {
    "name": "Угадай марку",
    "short_name": "Марки",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f5f6f8",
    "theme_color": "#f5f6f8",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}
(docs / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

version = hashlib.sha1(site.encode()).hexdigest()[:10]   # новая сборка → новый кэш
sw = f"""const CACHE = "car-quiz-{version}";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
}});
self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET") return;
  e.respondWith(caches.match(e.request, {{ ignoreSearch: true }}).then(r => r || fetch(e.request)));
}});
"""
(docs / "sw.js").write_text(sw, encoding="utf-8")
(docs / ".nojekyll").write_text("", encoding="utf-8")

print(f"CarQuiz.html и docs/: {len(logos)} логотипов, {len(offline.encode()) / 1024 / 1024:.1f} МБ, кэш {version}")
