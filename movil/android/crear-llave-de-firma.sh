#!/bin/zsh
# Crea la llave para firmar la app de Android que se sube a Google Play ("llave de subida").
# Queda FUERA del repositorio (que es público), en ~/claves-app-yoel-migdal/.
# Se corre UNA sola vez:  zsh movil/android/crear-llave-de-firma.sh
set -e
source ~/.zshrc >/dev/null 2>&1 || true
D="$HOME/claves-app-yoel-migdal"
mkdir -p "$D" && chmod 700 "$D"
if [ -f "$D/subida.jks" ]; then
  echo "Ya existe una llave en $D. No se crea otra."
  exit 1
fi
echo "Elegí una clave para la llave (mínimo 6 caracteres) y anotala en un lugar seguro."
echo "Mientras la escribís no se ve nada en pantalla: es normal."
read -s "C?Clave: "; echo
read -s "C2?Repetila: "; echo
if [ "$C" != "$C2" ] || [ ${#C} -lt 6 ]; then
  echo "Las claves no coinciden o son muy cortas. Volvé a correr el programa."
  exit 1
fi
keytool -genkeypair -keystore "$D/subida.jks" -alias subida -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass "$C" -keypass "$C" -dname "CN=Yoel Migdal, O=Rabino Yoel Migdal, C=AR" >/dev/null
printf 'archivo=subida.jks\nalias=subida\nclave=%s\n' "$C" > "$D/firma.properties"
chmod 600 "$D/subida.jks" "$D/firma.properties"
echo ""
echo "Listo: la llave quedó en $D"
echo "IMPORTANTE: guardá una copia de esa carpeta en un lugar seguro (pendrive o nube privada)."
