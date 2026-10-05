#!/usr/bin/env python3
"""
Genera una página de "compartir" por cada shiur de data.json, para que al
pegar el enlace en WhatsApp / Telegram / etc. se vea la portada y el título
de ESE shiur.

Por qué hace falta: la web es una sola página (index.html) que arma todo con
JavaScript, y los programas que generan la vista previa de un enlace
(WhatsApp, Telegram, Facebook...) NO ejecutan JavaScript: solo leen el HTML
estático. Entonces cada shiur tiene su propio archivo s/<id>.html con las
etiquetas Open Graph (título, descripción, imagen) y un redirect inmediato al
shiur real (../?shiur=<id>). Las personas ni lo notan.

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
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = REPO_ROOT / "data.json"
PAGES_DIR = REPO_ROOT / "s"
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


def renderizar_pagina(shiur, imagen_url, con_medidas):
    id_ = str(shiur["id"])
    titulo = (shiur.get("titulo") or "").strip()
    descripcion = texto_vista_previa(shiur)
    url_pagina = f"{SITE_URL}s/{id_}.html"
    destino = f"../?shiur={id_}"
    medidas = (
        f'<meta property="og:image:width" content="{LADO_MINIATURA}">\n'
        f'<meta property="og:image:height" content="{LADO_MINIATURA}">\n'
        '<meta property="og:image:type" content="image/jpeg">\n'
        if con_medidas
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)} — Rabino Yoel Migdal</title>
<meta name="robots" content="noindex">
<meta name="description" content="{esc(descripcion)}">
<link rel="canonical" href="{esc(url_pagina)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Rabino Yoel Migdal — Shiurim">
<meta property="og:locale" content="es_ES">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(descripcion)}">
<meta property="og:url" content="{esc(url_pagina)}">
<meta property="og:image" content="{esc(imagen_url)}">
{medidas}<meta property="og:image:alt" content="Portada del shiur: {esc(titulo)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(titulo)}">
<meta name="twitter:description" content="{esc(descripcion)}">
<meta name="twitter:image" content="{esc(imagen_url)}">
<style>
  body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #F7F3EA; color: #211B13; font-family: Georgia, serif; text-align: center; padding: 24px; }}
  a {{ color: #1C2B4A; }}
</style>
<script>location.replace("{destino}");</script>
</head>
<body>
<p>Abriendo el shiur… <a href="{destino}">Tocá acá si no se abre solo</a></p>
</body>
</html>
"""


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    shiurim = [s for s in data.get("shiurim", []) if str(s.get("id", "")).isdigit() and s.get("titulo")]

    PAGES_DIR.mkdir(exist_ok=True)
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

    # 2) Una página por shiur (solo se escribe si cambió)
    escritas = 0
    paginas_esperadas = set()
    miniaturas_esperadas = set()
    for s in shiurim:
        miniatura = nombre_miniatura(s) if s.get("portadaUrl") else None
        hay_miniatura = bool(miniatura) and (THUMBS_DIR / miniatura).exists()
        if miniatura:
            miniaturas_esperadas.add(miniatura)
        imagen = f"{SITE_URL}og/{miniatura}" if hay_miniatura else IMAGEN_RESPALDO
        contenido = renderizar_pagina(s, imagen, hay_miniatura)
        archivo = PAGES_DIR / f"{s['id']}.html"
        paginas_esperadas.add(archivo.name)
        if not archivo.exists() or archivo.read_text(encoding="utf-8") != contenido:
            archivo.write_text(contenido, encoding="utf-8")
            escritas += 1

    # 3) Limpieza: shiurim eliminados o portadas reemplazadas
    borradas = 0
    for archivo in PAGES_DIR.glob("*.html"):
        if archivo.name not in paginas_esperadas:
            archivo.unlink()
            borradas += 1
    for archivo in THUMBS_DIR.glob("*.jpg"):
        if archivo.name not in miniaturas_esperadas:
            archivo.unlink()
            borradas += 1

    print(
        f"Páginas de compartir: {len(shiurim)} shiurim ({escritas} escrita(s)/actualizada(s), "
        f"{creadas} miniatura(s) nueva(s), {borradas} archivo(s) viejo(s) borrado(s))."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # nunca debe impedir que se publique data.json
        print(f"ERROR generando páginas de compartir: {e}", file=sys.stderr)
        sys.exit(1)
