// Genera las imágenes base del ícono y la pantalla de inicio a partir del logo de la web
// (../icons/logo-ym.svg, con los colores del ícono de la web: libro claro sobre fondo oscuro).
// Después capacitor-assets las convierte a todos los tamaños de iOS y Android.
// Uso: npm run iconos
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import sharp from 'sharp';

const OSCURO = '#211B13';
const CLARO = '#F7F3EA';
const DORADO = '#C79A4B';

// Logo de la web con los colores invertidos (como en icons/icon-512.png)
const logo = readFileSync(new URL('../icons/logo-ym.svg', import.meta.url), 'utf8')
  .replace(/^<svg[^>]*>/, '')
  .replace(/<\/svg>\s*$/, '')
  .replaceAll('#F7F3EA', '__LETRAS__')
  .replaceAll('#211B13', CLARO)
  .replaceAll('__LETRAS__', OSCURO)
  .replaceAll('#B8863B', DORADO);

// viewBox del logo: x 10..90, y 12..84 (80 x 72)
function svg(lado, anchoLogo, fondo) {
  const escala = anchoLogo / 80;
  const x = (lado - anchoLogo) / 2 - 10 * escala;
  const y = (lado - 72 * escala) / 2 - 12 * escala;
  const rect = fondo ? `<rect width="${lado}" height="${lado}" fill="${fondo}"/>` : '';
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${lado}" height="${lado}">${rect}` +
    `<g transform="translate(${x} ${y}) scale(${escala})">${logo}</g></svg>`);
}

async function png(nombre, buffer, opaco) {
  let img = sharp(buffer);
  if (opaco) img = img.flatten({ background: OSCURO });
  await img.png().toFile(`assets/${nombre}`);
  console.log('assets/' + nombre);
}

// `node generar-iconos.mjs despues`: corrige lo que deja capacitor-assets en Android.
// Achica también el fondo del ícono adaptativo y queda un anillo sin fondo: se usa un color liso.
if (process.argv[2] === 'despues') {
  const res = 'android/app/src/main/res/';
  for (const f of ['ic_launcher.xml', 'ic_launcher_round.xml']) {
    const p = res + 'mipmap-anydpi-v26/' + f;
    writeFileSync(p, readFileSync(p, 'utf8').replace(
      /<background>[\s\S]*?<\/background>/,
      '<background android:drawable="@color/ic_launcher_background" />'));
  }
  const color = res + 'values/ic_launcher_background.xml';
  writeFileSync(color, readFileSync(color, 'utf8').replace(/#[0-9A-Fa-f]{6}/, OSCURO));
  process.exit(0);
}

mkdirSync('assets', { recursive: true });
// Ícono (iOS no admite transparencia)
await png('icon-only.png', svg(1024, 640, OSCURO), true);
// Android "adaptativo": logo + fondo liso aparte (capacitor-assets lo achica a la zona segura)
await png('icon-foreground.png', svg(1024, 700, null), false);
await png('icon-background.png', svg(1024, 0, OSCURO), true);
// Pantalla de inicio (la misma en modo claro y oscuro)
await png('splash.png', svg(2732, 620, OSCURO), true);
await png('splash-dark.png', svg(2732, 620, OSCURO), true);
