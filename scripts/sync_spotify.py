#!/usr/bin/env python3
"""
Sincroniza data.json con el feed RSS de Spotify/Anchor del podcast.

Replica exactamente la lógica de importación por RSS del Panel Admin
(ver parsearFeedRSS / detectarCategoria / handleSyncRss en index.html):
  - Un episodio nuevo (audioUrl que no existe todavía en data.json) se agrega
    con categoría detectada automáticamente por palabras clave.
  - Un episodio ya existente (mismo audioUrl) se actualiza en título, portada,
    fecha y descripción, pero conserva id, categoría (por si se corrigió a
    mano) y reproducciones.
  - Nunca se borra nada: si un episodio desaparece del feed, sigue en
    data.json.

Solo usa la librería estándar de Python (sin dependencias externas) para que
el workflow de GitHub Actions no necesite instalar nada.
"""
import json
import re
import sys
import unicodedata
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = REPO_ROOT / "data.json"
FEED_FALLBACK_URL = "https://anchor.fm/s/2fd6a950/podcast/rss"

NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}

REGLAS_CATEGORIA = [
    ("Tania", ["tania"]),
    ("Pirkei Avot", ["pirkei avot", "pirke avot", "avot"]),
    (
        "Historias Jasídicas",
        ["historias jasidicas", "historia jasidica", "cuento jasidico", "relato jasidico", "anecdota jasidica"],
    ),
    ("Discursos Jasídicos", ["discursos jasidicos", "discurso jasidico", "maamar", "dvar maljut"]),
    (
        "Fechas especiales",
        [
            "rosh hashana", "iom kipur", "yom kipur", "kipur", "sucot", "sukkot", "pesaj", "pesach",
            "shavuot", "shavuos", "purim", "januca", "hanuka", "hanukkah", "tisha b av", "tisha bav",
            "lag baomer", "tu bishvat", "tu bshvat", "simjat tora", "shmini atzeret", "rosh jodesh",
        ],
    ),
    ("Parashá de la semana", ["parasha de la semana", "parashat", "parasha", "parshat", "parsha"]),
    ("Conferencias", ["conferencia"]),
    ("Historia judía", ["historia judia"]),
    ("Pensamientos", ["pensamiento"]),
]
CATEGORIA_POR_DEFECTO = "Pensamientos"


def quitar_acentos(s):
    s = s or ""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def detectar_categoria(titulo, descripcion):
    texto = quitar_acentos(f"{titulo} {descripcion}")
    for categoria, palabras in REGLAS_CATEGORIA:
        if any(quitar_acentos(p) in texto for p in palabras):
            return categoria
    return CATEGORIA_POR_DEFECTO


def strip_html(html):
    texto = re.sub(r"<[^>]+>", " ", html or "")
    texto = re.sub(r"\s+", " ", texto)
    import html as html_module
    return html_module.unescape(texto).strip()


def texto_de(nodo, tag, ns=None):
    el = nodo.find(tag, ns) if ns else nodo.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def fetch_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ShiurimSync/1.0)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parsear_feed_rss(xml_bytes):
    root = ElementTree.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("El feed no tiene <channel>.")

    imagen_canal = texto_de(channel, "image/url")
    if not imagen_canal:
        itunes_img = channel.find("itunes:image", NS)
        imagen_canal = itunes_img.get("href", "") if itunes_img is not None else ""

    episodios = []
    for item in channel.findall("item"):
        enclosure = item.find("enclosure")
        audio_url = enclosure.get("url", "") if enclosure is not None else ""
        if not audio_url:
            continue  # se descartan entradas sin audio, igual que en el Panel Admin

        titulo = texto_de(item, "title") or "Episodio sin título"

        itunes_img = item.find("itunes:image", NS)
        portada_url = (itunes_img.get("href", "") if itunes_img is not None else "") or imagen_canal

        pub_date_raw = texto_de(item, "pubDate")
        fecha = ""
        if pub_date_raw:
            try:
                dt = parsedate_to_datetime(pub_date_raw)
                fecha = dt.date().isoformat()
            except (TypeError, ValueError):
                fecha = ""

        desc_raw = texto_de(item, "description")
        if not desc_raw:
            desc_raw = texto_de(item, "itunes:summary", NS)
        descripcion = strip_html(desc_raw)

        categoria = detectar_categoria(titulo, descripcion)
        episodios.append(
            {
                "titulo": titulo,
                "categoria": categoria,
                "audioUrl": audio_url,
                "portadaUrl": portada_url,
                "fecha": fecha,
                "descripcion": descripcion,
            }
        )
    return episodios


def sincronizar(data, episodios):
    shiurim = data.setdefault("shiurim", [])
    por_audio = {s.get("audioUrl"): s for s in shiurim}
    agregados = 0
    actualizados = 0
    base_id = int(__import__("time").time() * 1000)

    for idx, ep in enumerate(episodios):
        existente = por_audio.get(ep["audioUrl"])
        if existente:
            antes = (existente.get("titulo"), existente.get("portadaUrl"), existente.get("fecha"), existente.get("descripcion"))
            existente["titulo"] = ep["titulo"] or existente.get("titulo")
            existente["portadaUrl"] = ep["portadaUrl"] or existente.get("portadaUrl")
            existente["fecha"] = ep["fecha"] or existente.get("fecha")
            existente["descripcion"] = ep["descripcion"] or existente.get("descripcion")
            despues = (existente.get("titulo"), existente.get("portadaUrl"), existente.get("fecha"), existente.get("descripcion"))
            if antes != despues:
                actualizados += 1
        else:
            nuevo = {
                "id": base_id + idx,
                "titulo": ep["titulo"],
                "categoria": ep["categoria"],
                "fecha": ep["fecha"],
                "audioUrl": ep["audioUrl"],
                "portadaUrl": ep["portadaUrl"],
                "descripcion": ep["descripcion"],
                "transcripcion": "",
                "reproducciones": 0,
            }
            shiurim.append(nuevo)
            por_audio[ep["audioUrl"]] = nuevo
            agregados += 1

    return agregados, actualizados


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    feed_url = (data.get("config", {}).get("rssFeedUrl") or "").strip() or FEED_FALLBACK_URL

    print(f"Leyendo feed: {feed_url}")
    try:
        xml_bytes = fetch_feed(feed_url)
    except Exception as e:
        print(f"ERROR: no se pudo leer el feed RSS: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        episodios = parsear_feed_rss(xml_bytes)
    except Exception as e:
        print(f"ERROR: no se pudo parsear el feed RSS: {e}", file=sys.stderr)
        sys.exit(1)

    if not episodios:
        print("El feed se leyó bien pero no se encontraron episodios con audio.")
        sys.exit(0)

    agregados, actualizados = sincronizar(data, episodios)
    # Sin salto de línea final: así, si no hay cambios reales, el archivo
    # queda byte a byte igual al original y el workflow no genera un commit vacío.
    DATA_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Listo: {len(episodios)} episodios en el feed ({agregados} nuevo(s), {actualizados} revisado(s)).")


if __name__ == "__main__":
    main()
