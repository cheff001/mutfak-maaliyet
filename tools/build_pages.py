#!/usr/bin/env python3
"""Tarif sayfalarını, kategori sayfalarını, tarif dizinini, sitemap.xml ve robots.txt dosyalarını üretir.
Kullanım: python3 tools/build_pages.py [temel_adres]
Tarif ya da alerjen verisi index.html içinde değişince yeniden çalıştır."""
import json, subprocess, sys, os, shutil, datetime, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://cheff001.github.io/mutfak-maaliyet").rstrip("/")
TODAY = datetime.date.today().isoformat()
d = json.loads(subprocess.check_output(["node", os.path.join(ROOT, "tools/extract.js"), os.path.join(ROOT, "index.html")]))
units = json.load(open(os.path.join(ROOT, "tools/units.json"), encoding="utf-8"))
ALGL = {a[0]: a[1] for a in d["algl"]}
ALG = d["alg"]
TR = str.maketrans({"İ": "i", "I": "ı"})
def fold(s):
    s = s.translate(TR).lower()
    for a, b in zip("ışğüöçâî", "isguocai"): s = s.replace(a, b)
    return s
def slug(t):
    out = ""
    for ch in fold(t): out += ch if ch.isalnum() and ch.isascii() else "-"
    while "--" in out: out = out.replace("--", "-")
    return out.strip("-")
def esc(x): return html.escape(str(x), quote=True)
def num(x):
    x = round(x, 1)
    return str(int(x)) if x == int(x) else str(x).replace(".", ",")
def qty(n, a):
    u = units.get(n, "kg")
    if u == "adet": return num(a) + " adet"
    if u == "lt": return (num(a / 1000) + " lt") if a >= 1000 else (num(a) + " ml")
    return (num(a / 1000) + " kg") if a >= 1000 else (num(a) + " g")

recipes = []
for line in d["raw"]:
    c, n, p, it = line.split("|")
    items = []
    for x in it.split(","):
        k, a = x.split(":"); items.append((k, float(a)))
    al = []
    for k, _ in items:
        for code in ALG.get(k, "").split(","):
            if code and ALGL[code] not in al: al.append(ALGL[code])
    recipes.append(dict(c=c, n=n, p=int(p), it=items, al=al, s=slug(n)))
slugs = [r["s"] for r in recipes]
assert len(set(slugs)) == len(slugs), "slug çakışması"
cats = {}
for r in recipes: cats.setdefault(r["c"], []).append(r)

CSS = """*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#16282c;background:#eceff1}
main{max-width:720px;margin:0 auto;padding:18px 16px 40px}a{color:#0e6f68}
header.top{background:#0e6f68;color:#fff;padding:12px 16px}header.top a{color:#fff;text-decoration:none;font-weight:700}
.card{background:#fff;border:1px solid #d3dcde;border-radius:12px;padding:16px;margin:0 0 14px}
h1{font-family:Georgia,'Times New Roman',serif;font-size:28px;line-height:1.2;margin:8px 0 10px}h2{font-size:18px;margin:0 0 8px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px 6px;border-top:1px solid #d3dcde}th{border-top:0;color:#5d7176}td:last-child,th:last-child{text-align:right;white-space:nowrap}
.btn{display:inline-block;background:#0e6f68;color:#fff;text-decoration:none;font-weight:700;padding:13px 20px;border-radius:12px;margin:6px 0}
.note{color:#5d7176;font-size:14px}.al{display:inline-block;background:#fbe3e1;color:#a3201b;border-radius:6px;padding:1px 8px;font-size:14px;font-weight:700;margin:2px 4px 2px 0}
ul.l{list-style:none;padding:0;margin:0;columns:2;column-gap:20px}ul.l li{padding:4px 0;break-inside:avoid}@media(max-width:520px){ul.l{columns:1}}
footer{color:#5d7176;font-size:13px;margin-top:20px}"""
def page(title, desc, path, body, ld=None, depth=2):
    up = "../" * depth
    url = f"{BASE}/{path}"
    j = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}"><meta name="theme-color" content="#0e6f68">
<link rel="icon" type="image/png" href="{up}icon-192.png">
<meta property="og:type" content="website"><meta property="og:locale" content="tr_TR"><meta property="og:site_name" content="Mutfak Maliyet">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og.png"><meta name="twitter:card" content="summary_large_image">
<style>{CSS}</style>{j}</head><body>
<header class="top"><a href="{up}">Mutfak Maliyet</a></header><main>{body}
<footer><p>Mutfak Maliyet, restoran ve kafeler için ücretsiz reçete ve porsiyon maliyeti hesaplayıcıdır. Uygulama geliştirme aşamasındadır, fiyatlar şimdilik örnektir.</p>
<p><a href="{up}tarifler/">Tüm tarifler</a> · <a href="{up}">Uygulamayı aç</a></p></footer></main></body></html>"""

def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)

for d_ in ("tarif", "kategori", "tarifler"):
    shutil.rmtree(os.path.join(ROOT, d_), ignore_errors=True)

urls = [("", "1.0"), ("tarifler/", "0.8")]
for r in recipes:
    rel = [x for x in cats[r["c"]] if x["s"] != r["s"]][:8]
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{esc(qty(k, a))}</td></tr>" for k, a in r["it"])
    al = "".join(f'<span class="al">{esc(a)}</span>' for a in r["al"]) or "Bilinen alerjen kaynağı yok."
    links = "".join(f'<li><a href="../{x["s"]}/">{esc(x["n"])}</a></li>' for x in rel)
    ing_names = ", ".join(k.lower() if False else k for k, _ in r["it"][:4])
    body = f"""<p class="note"><a href="../../tarifler/">Tarifler</a> › <a href="../../kategori/{slug(r['c'])}/">{esc(r['c'])}</a></p>
<h1>{esc(r['n'])}: malzemeler ve porsiyon maliyeti</h1>
<p>{esc(r['n'])} tarifi {r['p']} porsiyonluktur. Aşağıdaki gramajlarla güncel maliyeti kendi fiyatlarınla hesaplayabilirsin.</p>
<p><a class="btn" href="../../?demo=1&amp;tarif={slug(r['n'])}">Maliyetini hesapla</a></p>
<div class="card"><h2>Malzemeler ({r['p']} porsiyon)</h2><table><tr><th>Malzeme</th><th>Miktar</th></tr>{rows}</table>
<p class="note">Gramajlar klasik ölçülerdir, işletmenin standart reçetesine göre değişebilir.</p></div>
<div class="card"><h2>Alerjenler</h2><p>{al}</p><p class="note">Sade ürünlere göre hazırlandı. Hazır ürünlerde ambalaj etiketini kontrol et.</p></div>
<div class="card"><h2>Maliyet nasıl hesaplanır?</h2><p>Her malzemenin birim fiyatı ile gramajı çarpılır, toplam porsiyon sayısına bölünür. Uygulamada Metro, market ve hâl fiyatlarını seçebilir ya da kendi faturandaki fiyatı girebilirsin. Fiyatlar şu an örnektir, kendi fiyatınla doğru sonucu görürsün.</p></div>
{('<div class="card"><h2>' + esc(r['c']) + ' kategorisindeki diğer tarifler</h2><ul class="l">' + links + '</ul></div>') if rel else ''}"""
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Tarifler", "item": f"{BASE}/tarifler/"},
        {"@type": "ListItem", "position": 2, "name": r["c"], "item": f"{BASE}/kategori/{slug(r['c'])}/"},
        {"@type": "ListItem", "position": 3, "name": r["n"], "item": f"{BASE}/tarif/{r['s']}/"}]}
    title = f"{r['n']} maliyeti ve malzemeleri | Mutfak Maliyet"
    desc = f"{r['n']} için malzeme listesi, gramajlar ve alerjen bilgisi. Porsiyon maliyetini kendi fiyatlarınla ücretsiz hesapla."
    write(f"tarif/{r['s']}/index.html", page(title, desc, f"tarif/{r['s']}/", body, ld))
    urls.append((f"tarif/{r['s']}/", "0.6"))

for c, rs in cats.items():
    lis = "".join(f'<li><a href="../../tarif/{x["s"]}/">{esc(x["n"])}</a></li>' for x in rs)
    body = f'<p class="note"><a href="../../tarifler/">Tarifler</a></p><h1>{esc(c)} tarifleri ve maliyetleri</h1><p>{len(rs)} tarif. Birini seç, malzemeleri ve alerjenleri gör, maliyetini hesapla.</p><div class="card"><ul class="l">{lis}</ul></div>'
    write(f"kategori/{slug(c)}/index.html", page(f"{c} tarifleri ve maliyetleri | Mutfak Maliyet", f"{c} kategorisinde {len(rs)} tarif: malzemeler, gramajlar, alerjenler ve porsiyon maliyeti hesaplama.", f"kategori/{slug(c)}/", body))
    urls.append((f"kategori/{slug(c)}/", "0.7"))

sec = ""
for c, rs in cats.items():
    lis = "".join(f'<li><a href="../tarif/{x["s"]}/">{esc(x["n"])}</a></li>' for x in rs)
    sec += f'<div class="card"><h2><a href="../kategori/{slug(c)}/">{esc(c)}</a> ({len(rs)})</h2><ul class="l">{lis}</ul></div>'
body = f'<h1>Tüm tarifler ve maliyet hesabı</h1><p>{len(recipes)} tarifin malzeme listesi, gramajları ve alerjenleri. Her tarifin porsiyon maliyetini uygulamada kendi fiyatlarınla hesaplayabilirsin.</p><p><a class="btn" href="../?demo=1">Uygulamayı dene</a></p>{sec}'
write("tarifler/index.html", page("Tüm tarifler ve maliyet hesabı | Mutfak Maliyet", f"{len(recipes)} tarifin malzemeleri, gramajları ve alerjenleri. Restoran ve kafe için porsiyon maliyeti hesaplayıcı.", "tarifler/", body, depth=1))

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u, pr in urls: sm += f"<url><loc>{BASE}/{u}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>\n"
sm += "</urlset>\n"
write("sitemap.xml", sm)
write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(len(recipes), "tarif,", len(cats), "kategori,", len(urls), "adres")
