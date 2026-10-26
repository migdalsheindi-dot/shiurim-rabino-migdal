#!/usr/bin/env python3
"""
Chequeo rápido (solo librería estándar, ~2 segundos): ¿hay algo nuevo en el feed de
Spotify que todavía no esté en data.json? Es lo primero que hace el workflow cada
pocos minutos, para no gastar tiempo instalando nada cuando no hay novedades.

Hay novedades si:
  - el feed tiene un episodio (audioUrl) que no está en data.json, o
  - el feed se regeneró (lastBuildDate) después del último que ya se aplicó
    (por ejemplo, se cambió una portada o un título en Creators).
Escribe novedad=true|false en $GITHUB_OUTPUT (y lo imprime).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_spotify import DATA_JSON, FEED_FALLBACK_URL, fecha_del_feed, fetch_feed, parsear_feed_rss  # noqa: E402


def salida(valor, motivo):
    print(f"novedad={valor} ({motivo})")
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(f"novedad={valor}\n")


def main():
    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    url = (data.get("config", {}).get("rssFeedUrl") or "").strip() or FEED_FALLBACK_URL
    try:
        xml = fetch_feed(url)
        episodios = parsear_feed_rss(xml)
    except Exception as e:  # si el feed falla, que la corrida completa lo informe
        salida("true", f"no se pudo leer el feed: {e}")
        return
    conocidos = {s.get("audioUrl") for s in data.get("shiurim", [])}
    nuevos = [e for e in episodios if e["audioUrl"] not in conocidos]
    if nuevos:
        salida("true", f"{len(nuevos)} episodio(s) nuevo(s): {nuevos[0]['titulo'][:50]}")
        return
    audios_feed = {e["audioUrl"] for e in episodios}
    if any(s.get("ausenteDesde") for s in data.get("shiurim", [])):
        salida("true", "hay shiurim marcados como ausentes del feed (se revisa si hay que retirarlos)")
        return
    fecha = fecha_del_feed(xml)
    aplicada = data.get("feedLastBuildDate", "")
    if fecha and fecha > aplicada:
        salida("true", f"el feed se regeneró ({fecha} > {aplicada or 'nunca'})")
        return
    salida("false", "sin cambios")


if __name__ == "__main__":
    main()
