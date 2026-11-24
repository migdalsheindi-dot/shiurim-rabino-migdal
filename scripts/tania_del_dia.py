#!/usr/bin/env python3
"""Tania del Día: prepara el texto hebreo del Tanya (Tanya Yomi) de los próximos días.

Fuente: Sefaria (https://www.sefaria.org), que publica el texto hebreo de Kehot Publication Society
con licencia CC BY-NC (hay que citar la fuente: la web lo hace) y el calendario del "Tanya Yomi",
que coincide con el de Chabad (verificado contra es.chabad.org para varios días).

Por qué no se toma el texto de es.chabad.org: esa página bloquea las consultas automáticas (desafío anti-robots) y
la traducción al español es contenido de Chabad.org. Para el español la web enlaza a su página del día.

Qué hace:
  1. Guarda una sola vez el texto hebreo de las cinco partes del Tanya en scripts/tania-he.json (lista ordenada de párrafos).
  2. Para cada día (de ayer a 8 días adelante) averigua dónde empieza el Tanya del día y dónde empieza el del
     día siguiente, y escribe tania/AAAA-MM-DD.json con los párrafos de ese tramo.
  3. Borra los archivos de días viejos.
Si algo falla (Sefaria no responde, cambia el formato...) no toca lo que ya estaba publicado y sale sin error:
la web igual funciona (mostrando solo el enlace a Chabad).

Uso:  python3 scripts/tania_del_dia.py            (los próximos días)
      python3 scripts/tania_del_dia.py --probar   (revisa todo un año sin escribir archivos)
"""
import html as html_module
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TEXTO_COMPLETO = RAIZ / "scripts" / "tania-he.json"
CARPETA = RAIZ / "tania"
SEFARIA = "https://www.sefaria.org/api"
DIAS_ATRAS = 1
DIAS_ADELANTE = 8
FUENTE = "Kehot Publication Society, vía Sefaria (licencia CC BY-NC)"

# Partes del Tanya en el orden en que se estudian: (prefijo de la referencia en Sefaria, profundidad, nombre en español, nombre del capítulo)
NODOS = [
    ("Tanya, Part I; Likkutei Amarim, Title Page", 1, "Likutei Amarim · Portada", None),
    ("Tanya, Part I; Likkutei Amarim, Approbation", 2, "Likutei Amarim · Aprobaciones", "Aprobación"),
    ("Tanya, Part I; Likkutei Amarim, Compiler's Foreword", 1, "Likutei Amarim · Prefacio del compilador", None),
    ("Tanya, Part I; Likkutei Amarim", 2, "Likutei Amarim", "Cap."),
    ("Tanya, Part II; Shaar HaYichud VehaEmunah, Chinukh Katan", 1, "Shaar HaYijud VeHaEmuná · Introducción", None),
    ("Tanya, Part II; Shaar HaYichud VehaEmunah", 2, "Shaar HaYijud VeHaEmuná", "Cap."),
    ("Tanya, Part III; Iggeret HaTeshuvah", 2, "Igueret HaTeshuvá", "Cap."),
    ("Tanya, Part IV; Iggeret HaKodesh", 2, "Igueret HaKodesh", "Carta"),
    ("Tanya, Part V; Kuntres Acharon", 2, "Kuntres Ajarón", "Ensayo"),
]


def descargar_json(url):
    """GET que devuelve JSON. Si Python no tiene certificados (pasa en algunas Mac), usa curl."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "yoelmigdal.com tania-del-dia (+https://yoelmigdal.com)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        out = subprocess.run(["curl", "-sf", "--max-time", "60", url], capture_output=True, text=True, check=True).stdout
        return json.loads(out)


def limpiar(texto):
    """Quita notas al pie, marcas de página y etiquetas; deja solo texto y <b> (las palabras iniciales en negrita)."""
    t = re.sub(r"<i[^>]*class=\"footnote\"[^>]*>.*?</i>", "", texto, flags=re.S)
    t = re.sub(r"<sup[^>]*>.*?</sup>", "", t, flags=re.S)
    t = re.sub(r"<i[^>]*data-overlay[^>]*>\s*</i>", "", t)
    t = re.sub(r"<\s*b\s*>", "\x01", t, flags=re.I)
    t = re.sub(r"<\s*/\s*b\s*>", "\x02", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html_module.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    t = html_module.escape(t, quote=False)
    return t.replace("\x01", "<b>").replace("\x02", "</b>")


def aplanar(valor, ruta, salida):
    """Convierte la lista anidada de Sefaria en una lista plana de (índices, texto)."""
    if isinstance(valor, str):
        salida.append((ruta, valor))
    elif isinstance(valor, list):
        for i, v in enumerate(valor, 1):
            aplanar(v, ruta + [i], salida)


def construir_texto_completo():
    plano = []
    for prefijo, profundidad, nombre, capitulo in NODOS:
        r = descargar_json(f"{SEFARIA}/v3/texts/{urllib.parse.quote(prefijo, safe=',;')}?version=hebrew")
        texto = r["versions"][0]["text"]
        partes = []
        aplanar(texto, [], partes)
        for indices, t in partes:
            limpio = limpiar(t)
            if not limpio:
                continue
            ref = f"{prefijo} {':'.join(str(i) for i in indices)}"
            plano.append({"ref": ref, "n": nombre, "c": capitulo, "i": indices, "t": limpio})
    if len(plano) < 1000:
        raise RuntimeError(f"El texto del Tanya salió demasiado corto ({len(plano)} párrafos)")
    return plano


def completar(p):
    """A partir de la referencia, recupera el nombre de la obra, el tipo de capítulo y los índices."""
    for prefijo, _, nombre, capitulo in NODOS:
        if p["ref"].startswith(prefijo + " "):
            resto = p["ref"][len(prefijo) + 1:]
            if re.fullmatch(r"[\d:]+", resto):
                return {**p, "n": nombre, "c": capitulo, "i": [int(x) for x in resto.split(":")]}
    raise RuntimeError(f"Referencia desconocida en tania-he.json: {p['ref']}")


def cargar_texto_completo():
    if TEXTO_COMPLETO.exists():
        return [completar(p) for p in json.loads(TEXTO_COMPLETO.read_text(encoding="utf-8"))]
    plano = construir_texto_completo()
    TEXTO_COMPLETO.write_text(json.dumps([{"ref": p["ref"], "t": p["t"]} for p in plano], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return plano


def inicio_del_dia(d):
    """Referencia (Sefaria) donde empieza el Tanya del día, y el nombre del día hebreo, p. ej. '14 Kislev'."""
    j = descargar_json(f"{SEFARIA}/calendars?diaspora=1&year={d.year}&month={d.month}&day={d.day}")
    for it in j.get("calendar_items", []):
        if it.get("title", {}).get("en") == "Tanya Yomi":
            return it["ref"], it["displayValue"]["en"]
    raise RuntimeError(f"Sefaria no informa el Tanya Yomi del {d}")


def etiqueta(item):
    """'Likutei Amarim · Cap. 18' (o Ensayo/Carta/Aprobación) a partir de un párrafo."""
    if item["c"] and item["i"]:
        return f"{item['n']} · {item['c']} {item['i'][0]}" if item["c"] != "Aprobación" else item["n"]
    return item["n"]


def tramo(plano, indice_ref, ref_inicio, ref_siguiente):
    s = indice_ref.get(ref_inicio)
    e = indice_ref.get(ref_siguiente)
    if s is None or e is None:
        raise RuntimeError(f"No encuentro en el texto la referencia {ref_inicio if s is None else ref_siguiente}")
    return plano[s:e] if e > s else plano[s:]  # el último día del ciclo llega hasta el final de la obra


def generar(dias_atras=DIAS_ATRAS, dias_adelante=DIAS_ADELANTE, escribir=True, hoy=None):
    plano = cargar_texto_completo()
    indice_ref = {p["ref"]: k for k, p in enumerate(plano)}
    hoy = hoy or datetime.now(timezone(timedelta(hours=-3))).date()  # hora de Argentina
    fechas = [hoy + timedelta(days=k) for k in range(-dias_atras, dias_adelante + 1)]
    refs = {d: inicio_del_dia(d) for d in fechas + [fechas[-1] + timedelta(days=1)]}
    if escribir:
        CARPETA.mkdir(exist_ok=True)
    escritos = 0
    for d in fechas:
        ref, hebreo = refs[d]
        siguiente, _ = refs[d + timedelta(days=1)]
        partes = tramo(plano, indice_ref, ref, siguiente)
        if not partes:
            raise RuntimeError(f"El tramo del {d} salió vacío")
        primero, ultimo = etiqueta(partes[0]), etiqueta(partes[-1])
        dato = {
            "fecha": d.isoformat(),
            "hebreo": hebreo,
            "referencia": primero if primero == ultimo else f"{primero} – {ultimo.split(' · ', 1)[-1]}",
            "parrafos": [p["t"] for p in partes],
            "fuente": FUENTE,
        }
        if escribir:
            ruta = CARPETA / f"{d.isoformat()}.json"
            nuevo = json.dumps(dato, ensure_ascii=False, separators=(",", ":"))
            if not ruta.exists() or ruta.read_text(encoding="utf-8") != nuevo:
                ruta.write_text(nuevo, encoding="utf-8")
                escritos += 1
    if escribir:
        limite = hoy - timedelta(days=dias_atras + 2)
        for f in CARPETA.glob("*.json"):
            try:
                if date.fromisoformat(f.stem) < limite:
                    f.unlink()
            except ValueError:
                pass
    return escritos


def probar_un_anio():
    """Revisa 400 días seguidos (sin escribir): todos tienen que dar un tramo no vacío, también en los cambios de obra."""
    plano = cargar_texto_completo()
    indice_ref = {p["ref"]: k for k, p in enumerate(plano)}
    desde = datetime.now(timezone(timedelta(hours=-3))).date()
    refs = [(desde + timedelta(days=k),) + inicio_del_dia(desde + timedelta(days=k)) for k in range(401)]
    mal = 0
    vistos = set()
    for k in range(400):
        d, ref, _ = refs[k]
        try:
            partes = tramo(plano, indice_ref, ref, refs[k + 1][1])
            assert partes
            vistos.add(len(partes))
        except Exception as e:
            mal += 1
            print("FALLA", d, ref, "->", refs[k + 1][1], e)
    print(f"{400 - mal}/400 días bien; tramo de {min(vistos)} a {max(vistos)} párrafos")
    return mal == 0


if __name__ == "__main__":
    try:
        if "--probar" in sys.argv:
            sys.exit(0 if probar_un_anio() else 1)
        print(f"Tania del día: {generar()} archivo(s) escrito(s)/actualizado(s) en tania/")
    except Exception as e:  # no romper la sincronización de los shiurim por esto
        print(f"AVISO: no se pudo preparar el Tania del día ({e}). Se deja lo que ya estaba.")
