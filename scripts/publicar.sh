#!/usr/bin/env bash
# Sube a GitHub lo que haya cambiado (datos, transcripciones, páginas y sitemap).
# Uso: scripts/publicar.sh "mensaje del commit"
set -e
mkdir -p transcripts s t og
git add data.json data-lite.json transcripts/ s/ t/ og/ sitemap.xml robots.txt
if git diff --cached --quiet; then
  echo "Sin cambios: ya estaba todo al día."
  exit 0
fi
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git commit -m "$1 [skip ci]"
# Si alguien subió algo mientras tanto, se integra antes de subir (hasta 3 intentos)
for intento in 1 2 3; do
  git pull --rebase --autostash -q && git push && exit 0
  echo "No se pudo subir (intento $intento), reintentando..."
  sleep 5
done
exit 1
