#!/usr/bin/env python3
"""
Genera las páginas estáticas del sitio para buscadores y para compartir:

  s/<id>.html      una página por shiur: título, portada, reproductor de audio,
                   descripción y transcripción en texto, datos estructurados
                   (JSON-LD) y etiquetas Open Graph. Es una página real e
                   indexable, así Google y WhatsApp leen el contenido sin
                   ejecutar JavaScript (la web principal es una sola página que
                   arma todo con JS). Desde ahí se puede abrir el shiur en la web
                   completa (?shiur=<id>).
  t/<slug>.html    una página por tema (categoría) con la lista de sus shiurim.
  sitemap.xml      inicio + temas + shiurim, con la fecha de cada uno.
  robots.txt       permite todo y apunta al sitemap.

Además, las portadas de Spotify pesan ~2 MB y WhatsApp descarta las imágenes
de vista previa de más de ~300 KB, así que se crea una miniatura liviana en
og/<id>-<hash>.jpg (el hash cambia si cambia la portada en Spotify, lo que
también evita que WhatsApp muestre una imagen vieja cacheada).

Es idempotente: si nada cambió, no reescribe ningún archivo (no genera
commits vacíos). Se corre en el workflow de sincronización, después de
sync_spotify.py, así las páginas de shiurim nuevos o editados quedan
publicadas en el mismo commit que data.json.

Dependencia opcional: Pillow (para las miniaturas). Si no está instalado, las
páginas igual se generan, con el ícono del sitio como imagen.
"""
import hashlib
import html
import io
import json
import os
import sys
import unicodedata
import urllib.request
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = REPO_ROOT / "data.json"
PAGES_DIR = REPO_ROOT / "s"
TEMAS_DIR = REPO_ROOT / "t"
THUMBS_DIR = REPO_ROOT / "og"

URL_GITHUB_PAGES = "https://migdalsheindi-dot.github.io/shiurim-rabino-migdal"


def url_del_sitio():
    # URL pública del sitio (con barra final). Las etiquetas og:url / og:image
    # tienen que ser absolutas. Prioridad: variable SITE_URL; si no hay, el
    # dominio propio del archivo CNAME (el que crea GitHub Pages al configurar
    # un dominio personalizado); si tampoco hay, la dirección de github.io.
    # Así, al comprar el dominio alcanza con agregar el CNAME: las páginas de
    # compartir se regeneran solas con la URL nueva en la próxima corrida.
    explicita = os.environ.get("SITE_URL", "").strip()
    if explicita:
        return explicita.rstrip("/") + "/"
    cname = REPO_ROOT / "CNAME"
    if cname.exists():
        lineas = cname.read_text(encoding="utf-8").split()
        if lineas:
            return f"https://{lineas[0]}/"
    return URL_GITHUB_PAGES + "/"


SITE_URL = url_del_sitio()
IMAGEN_RESPALDO = SITE_URL + "icons/icon-512.png"

LADO_MINIATURA = 512
MAX_BYTES_MINIATURA = 150_000
MAX_CARACTERES_DESCRIPCION = 200


def separar_descripcion(descripcion_completa):
    # Mismo criterio que separarDescripcion() en index.html: la primera línea
    # es el subtítulo y el resto la descripción.
    texto = (descripcion_completa or "").strip()
    salto = texto.find("\n")
    if salto == -1:
        return "", texto
    return texto[:salto].strip(), texto[salto + 1:].strip()


def texto_vista_previa(shiur):
    subtitulo, descripcion = separar_descripcion(shiur.get("descripcion"))
    partes = [p for p in (subtitulo, " ".join(descripcion.split())) if p]
    texto = " — ".join(partes) or "Shiurim del Rabino Yoel Migdal"
    if len(texto) > MAX_CARACTERES_DESCRIPCION:
        texto = texto[: MAX_CARACTERES_DESCRIPCION - 1].rstrip() + "…"
    return texto


def nombre_miniatura(shiur):
    huella = hashlib.sha1(shiur["portadaUrl"].encode("utf-8")).hexdigest()[:8]
    return f"{shiur['id']}-{huella}.jpg"


def crear_miniatura(url, destino):
    from PIL import Image, ImageOps  # import acá: Pillow es opcional

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ShiurimSync/1.0)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        datos = resp.read()
    img = Image.open(io.BytesIO(datos))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = ImageOps.fit(img, (LADO_MINIATURA, LADO_MINIATURA), Image.LANCZOS)
    for calidad in (82, 74, 66, 58, 50):
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=calidad, optimize=True, progressive=True)
        if buf.tell() <= MAX_BYTES_MINIATURA:
            break
    tmp = destino.with_suffix(".tmp")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(destino)


def esc(valor):
    return html.escape(str(valor), quote=True)


NOMBRE_SITIO = "Rabino Yoel Migdal — Shiurim"
URL_SPOTIFY = "https://open.spotify.com/show/0ynx2JbmZm1HmqJ7lzKY7Q"
URL_INSTAGRAM = "https://www.instagram.com/yoelmigdal/"
URL_X = "https://x.com/yoelmigdal"
DEDICATORIA = "Leilui Nishmat Shaia ben Hersh wolf Z”L"

# Descripciones breves y neutras de cada tema (para su página y sus metadatos)
DESCRIPCION_TEMAS = {
    "Tania": "Clases sobre el Tania (Likutei Amarim), obra fundamental del pensamiento jasídico de Jabad, explicadas capítulo por capítulo por el Rabino Yoel Migdal.",
    "Parashá de la semana": "Shiurim sobre la Parashá semanal de la Torá, con enseñanzas de la Torá y la jasidut.",
    "Conferencias": "Conferencias y charlas del Rabino Yoel Migdal sobre judaísmo, la Torá y la vida cotidiana.",
    "Pensamientos": "Pensamientos breves del Rabino Yoel Migdal para reflexionar sobre la Torá.",
    "Historias Jasídicas": "Historias jasídicas y las enseñanzas que dejan, contadas por el Rabino Yoel Migdal.",
    "Pirkei Avot": "Clases sobre Pirkei Avot (Ética de los Padres), con sus enseñanzas explicadas por el Rabino Yoel Migdal.",
    "Fechas especiales": "Shiurim sobre las fiestas y fechas especiales del calendario judío.",
    "Discursos Jasídicos": "Discursos jasídicos explicados por el Rabino Yoel Migdal.",
    "Historia judía": "Clases de historia del pueblo judío del Rabino Yoel Migdal.",
}


def slug(texto):
    # Igual que slug() en index.html: sin tildes, minúsculas y guiones.
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    out = []
    for c in t:
        out.append(c if c.isalnum() else "-")
    return "-".join(p for p in "".join(out).split("-") if p)


def json_ld(datos):
    # </ se escapa para que un texto nunca pueda cerrar la etiqueta <script>
    return json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def acortar(texto, largo=158):
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= largo else texto[: largo - 1].rstrip() + "…"


def parrafos(texto, por_parrafo=6):
    # La transcripción viene como un solo bloque: se parte en párrafos de ~6 frases.
    import re
    frases = re.split(r"(?<=[.!?…])\s+", " ".join(str(texto or "").split()))
    return [" ".join(frases[i:i + por_parrafo]) for i in range(0, len(frases), por_parrafo) if frases[i:i + por_parrafo]]


ESTILO = """
  :root { --crema:#F7F3EA; --tinta:#211B13; --azul:#1C2B4A; --noche:#0B1428; --oro:#C79A4B; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--crema); color:var(--tinta); font-family:"Plus Jakarta Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.65; -webkit-font-smoothing:antialiased; }
  a { color:var(--azul); }
  header.sitio { background:#fff; border-bottom:1px solid rgba(28,43,74,.1); }
  header.sitio .in { max-width:960px; margin:0 auto; padding:14px 20px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
  header.sitio a.marca { display:flex; align-items:center; gap:10px; text-decoration:none; color:var(--tinta); font-family:"Playfair Display",Georgia,serif; font-size:19px; font-weight:600; line-height:1.15; }
  header.sitio img { width:40px; height:36px; }
  .boton { display:inline-flex; align-items:center; justify-content:center; min-height:44px; padding:0 22px; border-radius:999px; background:var(--azul); color:#fff; text-decoration:none; font-weight:600; font-size:14px; }
  .boton.claro { background:#fff; color:var(--azul); border:1px solid rgba(28,43,74,.25); }
  main { max-width:760px; margin:0 auto; padding:28px 20px 56px; }
  nav.migas { font-size:13px; color:#746850; margin-bottom:18px; }
  nav.migas a { color:#746850; }
  h1 { font-family:"Playfair Display",Georgia,serif; font-size:clamp(26px,5vw,38px); line-height:1.15; color:var(--azul); margin:6px 0 8px; font-weight:700; letter-spacing:-.01em; }
  h2 { font-family:"Playfair Display",Georgia,serif; color:var(--azul); font-size:22px; margin:34px 0 12px; }
  .sub { color:#665C46; font-size:17px; margin:0 0 6px; }
  .meta { color:#746850; font-size:14px; margin:0 0 20px; }
  .etiqueta { display:inline-block; font-size:11px; letter-spacing:.08em; text-transform:uppercase; background:#E9ECF3; color:var(--azul); padding:4px 11px; border-radius:999px; text-decoration:none; font-weight:600; }
  .portada { width:100%; max-width:340px; aspect-ratio:1; object-fit:cover; border-radius:20px; box-shadow:0 14px 40px -14px rgba(28,43,74,.4); display:block; margin:18px 0; }
  audio { width:100%; margin:6px 0 18px; }
  .acciones { display:flex; flex-wrap:wrap; gap:10px; margin:6px 0 10px; }
  details { background:#fff; border:1px solid rgba(28,43,74,.1); border-radius:16px; padding:6px 20px; margin-top:26px; }
  summary { cursor:pointer; font-weight:600; color:var(--azul); padding:12px 0; }
  details p { margin:0 0 14px; color:#332C21; }
  ul.lista { list-style:none; margin:0; padding:0; }
  ul.lista li { background:#fff; border:1px solid rgba(28,43,74,.08); border-radius:14px; margin:0 0 10px; padding:12px 16px; }
  ul.lista a { text-decoration:none; font-weight:600; display:block; }
  ul.lista small { color:#746850; }
  footer.dedicatoria { background:var(--noche); text-align:center; padding:34px 20px 38px; }
  footer.dedicatoria i { display:block; width:64px; height:1px; margin:0 auto 18px; background:linear-gradient(90deg,transparent,var(--oro),transparent); }
  footer.dedicatoria p { margin:0; font-family:"Playfair Display",Georgia,serif; font-style:italic; color:rgba(244,231,198,.92); font-size:16px; letter-spacing:.02em; }
"""


def formatear_fecha(iso):
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    try:
        y, m, d = (int(x) for x in str(iso)[:10].split("-"))
        return f"{d} de {meses[m - 1]} de {y}"
    except Exception:
        return ""


def pagina(titulo, descripcion, canonical, cuerpo, jsonld, imagen=None, og_tipo="website", palabras=None, medidas=""):
    imagen = imagen or IMAGEN_RESPALDO
    keywords = ", ".join(palabras or ["shiurim", "Torá", "judaísmo", "Tania", "Parashá", "jasidut", "Rabino Yoel Migdal"])
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(descripcion)}">
<meta name="keywords" content="{esc(keywords)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" href="../favicon.ico" sizes="48x48">
<link rel="icon" type="image/svg+xml" href="../icons/logo-icon.svg">
<link rel="apple-touch-icon" href="../icons/apple-touch-icon.png">
<meta name="theme-color" content="#211b13">
<meta property="og:type" content="{og_tipo}">
<meta property="og:site_name" content="{esc(NOMBRE_SITIO)}">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(descripcion)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(imagen)}">
{medidas}<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(titulo)}">
<meta name="twitter:description" content="{esc(descripcion)}">
<meta name="twitter:image" content="{esc(imagen)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>{ESTILO}</style>
<script type="application/ld+json">{json_ld(jsonld)}</script>
</head>
<body>
<header class="sitio"><div class="in">
  <a class="marca" href="../"><img src="../icons/logo-ym.svg" alt="" width="40" height="36"><span>Rabino<br>Yoel Migdal</span></a>
  <a class="boton" href="../" style="white-space:nowrap">Ver shiurim</a>
</div></header>
<main>
{cuerpo}
</main>
<footer class="dedicatoria"><i></i><p>{esc(DEDICATORIA)}</p></footer>
</body>
</html>
"""


def serie_ld(rss=""):
    d = {
        "@type": "PodcastSeries",
        "@id": SITE_URL + "#serie",
        "name": "Rabino Yoel Migdal — Shiurim",
        "url": SITE_URL,
        "inLanguage": "es",
        "sameAs": [URL_SPOTIFY],
        "author": {"@id": SITE_URL + "#rabino"},
    }
    if rss:
        d["webFeed"] = rss
    return d


def persona_ld():
    return {
        "@type": "Person",
        "@id": SITE_URL + "#rabino",
        "name": "Rabino Yoel Migdal",
        "jobTitle": "Director de ISEJ",
        "url": SITE_URL,
        "sameAs": [URL_INSTAGRAM, URL_X],
    }


def renderizar_pagina(shiur, imagen_url, con_medidas, mismo_tema, rss=""):
    id_ = str(shiur["id"])
    titulo = (shiur.get("titulo") or "").strip()
    subtitulo, descripcion_larga = separar_descripcion(shiur.get("descripcion"))
    descripcion = acortar(texto_vista_previa(shiur))
    url_pagina = f"{SITE_URL}s/{id_}.html"
    tema = shiur.get("categoria") or ""
    url_tema = f"{SITE_URL}t/{slug(tema)}.html"
    audio = shiur.get("audioUrl") or ""
    fecha = str(shiur.get("fecha") or "")[:10]
    medidas = (
        f'<meta property="og:image:width" content="{LADO_MINIATURA}">\n'
        f'<meta property="og:image:height" content="{LADO_MINIATURA}">\n'
        '<meta property="og:image:type" content="image/jpeg">\n'
        if con_medidas
        else ""
    )

    episodio = {
        "@type": "PodcastEpisode",
        "name": titulo,
        "url": url_pagina,
        "inLanguage": "es",
        "description": descripcion,
        "image": imagen_url,
        "partOfSeries": serie_ld(rss),
        "author": persona_ld(),
    }
    if fecha:
        episodio["datePublished"] = fecha
    if audio:
        episodio["associatedMedia"] = {"@type": "AudioObject", "contentUrl": audio, "encodingFormat": "audio/mpeg", "name": titulo}
    migas = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": tema, "item": url_tema},
            {"@type": "ListItem", "position": 3, "name": titulo, "item": url_pagina},
        ],
    }
    jsonld = {"@context": "https://schema.org", "@graph": [episodio, migas]}

    partes = [
        f'<nav class="migas"><a href="../">Inicio</a> › <a href="../t/{esc(slug(tema))}.html">{esc(tema)}</a></nav>',
        f'<a class="etiqueta" href="../t/{esc(slug(tema))}.html">{esc(tema)}</a>',
        f"<h1>{esc(titulo)}</h1>",
    ]
    if subtitulo:
        partes.append(f'<p class="sub">{esc(subtitulo)}</p>')
    partes.append(f'<p class="meta">Rabino Yoel Migdal · {esc(formatear_fecha(fecha))}</p>')
    if imagen_url:
        partes.append(f'<img class="portada" src="{esc(imagen_url)}" alt="Portada del shiur: {esc(titulo)}" width="340" height="340">')
    if audio:
        partes.append(f'<audio controls preload="none" src="{esc(audio)}">Tu navegador no puede reproducir audio.</audio>')
    partes.append(
        f'<div class="acciones"><a class="boton" href="../?shiur={esc(id_)}">Escuchar en la web completa</a>'
        f'<a class="boton claro" href="../t/{esc(slug(tema))}.html">Más shiurim de {esc(tema)}</a></div>'
    )
    if descripcion_larga:
        partes.append("<h2>Sobre este shiur</h2>")
        partes.extend(f"<p>{esc(p)}</p>" for p in descripcion_larga.split("\n") if p.strip())
    transcripcion = parrafos(shiur.get("transcripcion"))
    if transcripcion:
        partes.append('<details><summary>Leer la transcripción</summary>')
        partes.extend(f"<p>{esc(p)}</p>" for p in transcripcion)
        partes.append("</details>")
    if mismo_tema:
        partes.append(f"<h2>Más de {esc(tema)}</h2><ul class=\"lista\">")
        for o in mismo_tema:
            partes.append(f'<li><a href="{esc(o["id"])}.html">{esc(o["titulo"])}</a><small>{esc(formatear_fecha(o["fecha"]))}</small></li>')
        partes.append("</ul>")

    palabras = ["shiur", "Torá", "judaísmo", tema, "Rabino Yoel Migdal", "clases de Torá", "jasidut"]
    return pagina(f"{titulo} | Rabino Yoel Migdal", descripcion, url_pagina, "\n".join(partes), jsonld, imagen_url, "article", palabras, medidas)


def renderizar_tema(tema, items, rss=""):
    s_ = slug(tema)
    url_pagina = f"{SITE_URL}t/{s_}.html"
    descripcion = DESCRIPCION_TEMAS.get(tema, f"Shiurim de {tema} del Rabino Yoel Migdal.")
    titulo = f"{tema}: shiurim y clases | Rabino Yoel Migdal"
    lista = {
        "@type": "ItemList",
        "numberOfItems": len(items),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{SITE_URL}s/{it['id']}.html", "name": it["titulo"]}
            for i, it in enumerate(items)
        ],
    }
    pagina_ld = {
        "@type": "CollectionPage",
        "name": f"{tema} — Rabino Yoel Migdal",
        "url": url_pagina,
        "description": descripcion,
        "inLanguage": "es",
        "isPartOf": {"@id": SITE_URL + "#sitio"},
        "mainEntity": lista,
    }
    migas = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": tema, "item": url_pagina},
        ],
    }
    cuerpo = [
        '<nav class="migas"><a href="../">Inicio</a></nav>',
        f"<h1>{esc(tema)}</h1>",
        f'<p class="sub">{esc(descripcion)}</p>',
        f'<p class="meta">{len(items)} {"shiur" if len(items) == 1 else "shiurim"}</p>',
        f'<div class="acciones"><a class="boton" href="../?tema={esc(s_)}">Abrir en la web completa</a></div>',
        '<ul class="lista" style="margin-top:22px">',
    ]
    for it in items:
        cuerpo.append(f'<li><a href="../s/{esc(it["id"])}.html">{esc(it["titulo"])}</a><small>{esc(formatear_fecha(it["fecha"]))}</small></li>')
    cuerpo.append("</ul>")
    return pagina(titulo, acortar(descripcion), url_pagina, "\n".join(cuerpo), {"@context": "https://schema.org", "@graph": [pagina_ld, migas]}, None, "website", [tema, "shiurim", "Torá", "Rabino Yoel Migdal"])


def escribir_si_cambio(archivo, contenido):
    if not archivo.exists() or archivo.read_text(encoding="utf-8") != contenido:
        archivo.write_text(contenido, encoding="utf-8")
        return True
    return False


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    shiurim = [s for s in data.get("shiurim", []) if str(s.get("id", "")).isdigit() and s.get("titulo")]
    rss = (data.get("config") or {}).get("rssFeedUrl", "") or ""

    PAGES_DIR.mkdir(exist_ok=True)
    TEMAS_DIR.mkdir(exist_ok=True)
    THUMBS_DIR.mkdir(exist_ok=True)

    # 1) Miniaturas que faltan (solo se descargan las nuevas o las que cambiaron de portada)
    pendientes = [s for s in shiurim if s.get("portadaUrl") and not (THUMBS_DIR / nombre_miniatura(s)).exists()]
    creadas = 0
    if pendientes:
        try:
            import PIL  # noqa: F401
        except ImportError:
            print("Aviso: Pillow no está instalado; las páginas usarán el ícono del sitio como imagen.")
            pendientes = []

    def procesar(shiur):
        try:
            crear_miniatura(shiur["portadaUrl"], THUMBS_DIR / nombre_miniatura(shiur))
            return True
        except Exception as e:
            print(f"  No se pudo crear la miniatura de '{shiur['titulo'][:40]}': {e}")
            return False

    if pendientes:
        print(f"Creando {len(pendientes)} miniatura(s)...")
        with ThreadPoolExecutor(max_workers=6) as pool:
            creadas = sum(pool.map(procesar, pendientes))

    # Orden: más nuevos primero (para las listas por tema y "más de este tema")
    ordenados = sorted(shiurim, key=lambda x: str(x.get("fecha") or ""), reverse=True)
    por_tema = {}
    for s in ordenados:
        por_tema.setdefault(s.get("categoria") or "Otros", []).append(s)

    # 2) Una página por shiur (solo se escribe si cambió)
    escritas = 0
    paginas_esperadas = set()
    miniaturas_esperadas = set()
    for s in ordenados:
        miniatura = nombre_miniatura(s) if s.get("portadaUrl") else None
        hay_miniatura = bool(miniatura) and (THUMBS_DIR / miniatura).exists()
        if miniatura:
            miniaturas_esperadas.add(miniatura)
        imagen = f"{SITE_URL}og/{miniatura}" if hay_miniatura else IMAGEN_RESPALDO
        mismo_tema = [o for o in por_tema.get(s.get("categoria") or "Otros", []) if o["id"] != s["id"]][:5]
        contenido = renderizar_pagina(s, imagen, hay_miniatura, mismo_tema, rss)
        archivo = PAGES_DIR / f"{s['id']}.html"
        paginas_esperadas.add(archivo.name)
        escritas += escribir_si_cambio(archivo, contenido)

    # 3) Una página por tema
    temas_esperados = set()
    for tema, items in por_tema.items():
        archivo = TEMAS_DIR / f"{slug(tema)}.html"
        temas_esperados.add(archivo.name)
        escritas += escribir_si_cambio(archivo, renderizar_tema(tema, items, rss))

    # 4) sitemap.xml y robots.txt
    hoy = date.today().isoformat()
    ultima = str(ordenados[0].get("fecha") or hoy)[:10] if ordenados else hoy
    urls = [(SITE_URL, ultima, "1.0")]
    urls += [(f"{SITE_URL}t/{slug(t)}.html", str(items[0].get("fecha") or ultima)[:10], "0.8") for t, items in por_tema.items()]
    urls += [(f"{SITE_URL}s/{s['id']}.html", str(s.get("fecha") or ultima)[:10], "0.6") for s in ordenados]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{esc(u)}</loc><lastmod>{f}</lastmod><priority>{p}</priority></url>\n" for u, f, p in urls)
    sitemap += "</urlset>\n"
    escritas += escribir_si_cambio(REPO_ROOT / "sitemap.xml", sitemap)
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n"
    escritas += escribir_si_cambio(REPO_ROOT / "robots.txt", robots)

    # 5) Limpieza: shiurim eliminados o portadas reemplazadas
    borradas = 0
    for archivo in PAGES_DIR.glob("*.html"):
        if archivo.name not in paginas_esperadas:
            archivo.unlink()
            borradas += 1
    for archivo in TEMAS_DIR.glob("*.html"):
        if archivo.name not in temas_esperados:
            archivo.unlink()
            borradas += 1
    for archivo in THUMBS_DIR.glob("*.jpg"):
        if archivo.name not in miniaturas_esperadas:
            archivo.unlink()
            borradas += 1

    print(
        f"Páginas: {len(shiurim)} shiurim + {len(por_tema)} temas ({escritas} escrita(s)/actualizada(s), "
        f"{creadas} miniatura(s) nueva(s), {borradas} archivo(s) viejo(s) borrado(s))."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # nunca debe impedir que se publique data.json
        print(f"ERROR generando páginas de compartir: {e}", file=sys.stderr)
        sys.exit(1)
