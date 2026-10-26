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

Además, los episodios sin transcripción (los nuevos de esta corrida y,
cuando sobra cupo, shiurim viejos del backlog) se transcriben
automáticamente y gratis con Whisper corriendo localmente (ver
transcribe.py) — sin ninguna API paga. El texto va a data.json (campo
"transcripcion") y los tiempos por palabra a transcripts/{id}.json (los
usa el front para resaltar la palabra exacta en sincronía con el audio).
Solo esa parte necesita una dependencia externa (faster-whisper, instalada
por el workflow vía scripts/requirements.txt); el resto de este archivo usa
únicamente la librería estándar de Python.
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_JSON = REPO_ROOT / "data.json"
TRANSCRIPTS_DIR = REPO_ROOT / "transcripts"
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
    # El editor de Spotify for Creators separa "subtítulo" de "descripción"
    # con un párrafo aparte (</p><p>...), sin ningún espacio entre las
    # etiquetas. Por eso los cierres de <p>/<div> y los <br> se convierten a
    # salto de línea ANTES de sacar el resto de las etiquetas — si no, esa
    # separación se perdía (</p><p> quedaba como un simple espacio) y todo
    # el texto se veía pegado en un solo bloque en la web.
    texto = re.sub(r"<\s*/\s*(p|div)\s*>", "\n", html or "", flags=re.I)
    texto = re.sub(r"<\s*br\s*/?\s*>", "\n", texto, flags=re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"[ \t]*\n[ \t]*", "\n", texto)  # espacios pegados a saltos de línea
    texto = re.sub(r"\n{3,}", "\n\n", texto)  # como mucho una línea en blanco
    texto = re.sub(r"[ \t]+", " ", texto)
    import html as html_module
    return html_module.unescape(texto).strip()


def texto_de(nodo, tag, ns=None):
    el = nodo.find(tag, ns) if ns else nodo.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def fetch_feed(url):
    # El CDN de Spotify/Anchor guarda el feed en caché y cada servidor lo renueva
    # a destiempo: pedirlo "sin caché" y con un parámetro distinto cada vez ayuda
    # a recibir la versión más nueva (y abajo se descarta igual cualquier copia
    # más vieja que la ya aplicada).
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}cb={int(time.time() // 60)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ShiurimSync/1.0)",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fecha_del_feed(xml_bytes):
    # <lastBuildDate> del feed (cuándo se regeneró por última vez) como texto ISO UTC, o "".
    try:
        canal = ElementTree.fromstring(xml_bytes).find("channel")
        crudo = texto_de(canal, "lastBuildDate")
        dt = parsedate_to_datetime(crudo)
        from datetime import timezone
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return ""


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
    nuevos_shiurim = []
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
            nuevos_shiurim.append(nuevo)
            agregados += 1

    return agregados, actualizados, nuevos_shiurim


# Un episodio de Spotify que desaparece del feed (porque en Creators se borró o se
# reemplazó por otro) se retira de la web, pero solo con varias garantías:
#   - solo los que usan el audio de Spotify/Anchor del feed (los cargados a mano desde el
#     Panel Admin con otro enlace NO se tocan nunca),
#   - solo si el feed vino completo (no si llegó cortado o vacío),
#   - y solo si lleva ausente 24 horas seguidas (por si fue un error pasajero).
HORAS_AUSENTE_PARA_RETIRAR = 24
PROPORCION_MINIMA_FEED = 0.9


def retirar_ausentes(data, episodios):
    from datetime import datetime, timedelta, timezone

    ahora = datetime.now(timezone.utc)
    audios_feed = {e["audioUrl"] for e in episodios}
    patron = re.compile(r"^https://anchor\.fm/s/[^/]+/podcast/play/")
    ejemplo = next((e["audioUrl"] for e in episodios if patron.match(e["audioUrl"])), "")
    if not ejemplo:
        return []
    prefijo_serie = "/".join(ejemplo.split("/")[:5]) + "/podcast/play/"  # https://anchor.fm/s/<serie>/podcast/play/
    de_spotify = [s for s in data["shiurim"] if s.get("audioUrl", "").startswith(prefijo_serie)]
    if len(episodios) < PROPORCION_MINIMA_FEED * len(de_spotify):
        print("Aviso: el feed trae muchos menos episodios que la web; no se retira nada.")
        return []

    retirados = []
    for s in list(de_spotify):
        if s["audioUrl"] in audios_feed:
            s.pop("ausenteDesde", None)
            continue
        desde = s.get("ausenteDesde")
        if not desde:
            s["ausenteDesde"] = ahora.strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"Aviso: '{s['titulo'][:50]}' ya no está en el feed; se retira si sigue ausente {HORAS_AUSENTE_PARA_RETIRAR} h.")
            continue
        try:
            desde_dt = datetime.strptime(desde, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            s["ausenteDesde"] = ahora.strftime("%Y-%m-%dT%H:%M:%SZ")
            continue
        if ahora - desde_dt >= timedelta(hours=HORAS_AUSENTE_PARA_RETIRAR):
            data["shiurim"].remove(s)
            archivo = TRANSCRIPTS_DIR / f"{s['id']}.json"
            if archivo.exists():
                archivo.unlink()
            retirados.append(s)
            print(f"Retirado de la web (ya no está en Spotify): {s['titulo'][:60]}")
    return retirados


# Tope de seguridad: cuántos episodios se transcriben como máximo en una
# sola corrida (protege contra corridas larguísimas). Se priorizan siempre
# los episodios nuevos de esta corrida; el resto del cupo se usa para ir
# rellenando de a poco los shiurim viejos que todavía no tienen
# transcripción (backlog), así con el tiempo terminan teniéndola todos sin
# necesitar una corrida gigante de una sola vez.
MAX_TRANSCRIPCIONES_POR_CORRIDA = int(os.environ.get("MAX_TRANSCRIPCIONES_POR_CORRIDA", "5"))


def transcribir_pendientes(todos_los_shiurim, nuevos_shiurim):
    nuevos_ids = {s["id"] for s in nuevos_shiurim}
    backlog = [s for s in todos_los_shiurim if s["id"] not in nuevos_ids and not (s.get("transcripcion") or "").strip()]
    pendientes = (nuevos_shiurim + backlog)[:MAX_TRANSCRIPCIONES_POR_CORRIDA]
    if not pendientes:
        return 0

    total_sin_transcripcion = len(nuevos_shiurim) + len(backlog)
    if total_sin_transcripcion > MAX_TRANSCRIPCIONES_POR_CORRIDA:
        print(
            f"Aviso: hay {total_sin_transcripcion} episodios sin transcripción, pero el tope por corrida es "
            f"{MAX_TRANSCRIPCIONES_POR_CORRIDA}. El resto se va a ir completando en próximas corridas."
        )

    from transcribe import transcribir_audio_url

    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    hechas = 0
    for shiur in pendientes:
        print(f"Transcribiendo: {shiur['titulo']}...")
        try:
            resultado = transcribir_audio_url(shiur["audioUrl"])
            texto = resultado["texto"]
            if texto:
                shiur["transcripcion"] = texto
                archivo = TRANSCRIPTS_DIR / f"{shiur['id']}.json"
                archivo.write_text(
                    json.dumps({"palabras": resultado["palabras"]}, ensure_ascii=False),
                    encoding="utf-8",
                )
                hechas += 1
                print(f"  OK ({len(texto)} caracteres, {len(resultado['palabras'])} palabras con tiempos).")
            else:
                print("  Transcripción vacía, se deja el campo en blanco.")
        except Exception as e:
            print(f"  ERROR al transcribir '{shiur['titulo']}': {e}")
    return hechas


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    # data.json es público: el email que recibe las consultas del formulario
    # vive solo en EmailJS. Si alguna vez se cuela acá (por ejemplo desde un
    # backup viejo del Panel Admin), se saca en la próxima sincronización.
    data.get("config", {}).pop("adminEmail", None)
    feed_url =(data.get("config", {}).get("rssFeedUrl") or "").strip() or FEED_FALLBACK_URL

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

    # Si el servidor entregó una copia del feed MÁS VIEJA que la última que ya se
    # aplicó (pasa con las cachés del CDN), se ignora para no deshacer cambios
    # recientes, como portadas nuevas. La próxima corrida lo vuelve a intentar.
    fecha_feed = fecha_del_feed(xml_bytes)
    ultima_aplicada = data.get("feedLastBuildDate", "")
    if fecha_feed and ultima_aplicada and fecha_feed < ultima_aplicada:
        print(f"Aviso: el feed recibido ({fecha_feed}) es más viejo que el último aplicado ({ultima_aplicada}); se ignora.")
        agregados, actualizados, nuevos_shiurim = 0, 0, []
    else:
        agregados, actualizados, nuevos_shiurim = sincronizar(data, episodios)
        retirar_ausentes(data, episodios)
        if fecha_feed:
            data["feedLastBuildDate"] = fecha_feed

    transcritas = 0
    if os.environ.get("SKIP_TRANSCRIPCION") != "1":
        transcritas = transcribir_pendientes(data["shiurim"], nuevos_shiurim)

    # Sin salto de línea final: así, si no hay cambios reales, el archivo
    # queda byte a byte igual al original y el workflow no genera un commit vacío.
    DATA_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Listo: {len(episodios)} episodios en el feed ({agregados} nuevo(s), {actualizados} revisado(s), "
        f"{transcritas} transcripción(es) generada(s))."
    )


if __name__ == "__main__":
    main()
