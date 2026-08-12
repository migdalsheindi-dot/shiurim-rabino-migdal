#!/usr/bin/env python3
"""
Transcripción automática y gratuita de audio, usando Whisper corriendo
localmente (librería `faster-whisper`, de código abierto) — sin ninguna API
paga ni API key. Pensado para correr dentro del runner de GitHub Actions.
"""
import os
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")
_modelo = None


def _obtener_modelo():
    global _modelo
    if _modelo is None:
        from faster_whisper import WhisperModel
        print(f"Cargando modelo Whisper '{MODEL_SIZE}' (puede tardar la primera vez)...")
        _modelo = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return _modelo


def _extension_de(url):
    path = urlparse(url).path
    ext = Path(path).suffix
    return ext if ext and len(ext) <= 5 else ".m4a"


def _descargar_audio(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ShiurimSync/1.0)"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(destino, "wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def transcribir_audio_url(audio_url):
    """Descarga el audio de audio_url y devuelve el texto transcrito (o "" si falla)."""
    modelo = _obtener_modelo()
    with tempfile.TemporaryDirectory() as tmp:
        audio_path = Path(tmp) / f"audio{_extension_de(audio_url)}"
        _descargar_audio(audio_url, audio_path)
        segments, info = modelo.transcribe(
            str(audio_path),
            language="es",
            vad_filter=True,
            beam_size=5,
        )
        texto = " ".join(seg.text.strip() for seg in segments)
        return texto.strip()
