// Arma ../../privacidad.html (página pública de la web) a partir de politica-de-privacidad.md,
// con el mismo estilo que las páginas fijas de la web (t/, s/). Las líneas de aviso de borrador
// (las que empiezan con ">") no se publican.
// Uso: node movil/legal/generar-privacidad.mjs   (después, revisar y publicar la web)
import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const md = readFileSync(new URL('./politica-de-privacidad.md', import.meta.url), 'utf8')
  .split('\n')
  .filter((l) => !l.startsWith('>'))
  .join('\n')
  .replace(/^# .*\n/, ''); // el título va aparte, en el encabezado de la página
// marked ya convierte los correos en enlaces "mailto:"
const cuerpo = execFileSync('npx', ['-y', 'marked@15', '--gfm'], { input: md, encoding: 'utf8' });

const TITULO = 'Política de privacidad | Rabino Yoel Migdal';
const DESCRIPCION = 'Qué datos usan el sitio yoelmigdal.com y la aplicación del Rabino Yoel Migdal, para qué y cómo pedir que se borren.';

const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${TITULO}</title>
<meta name="description" content="${DESCRIPCION}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://yoelmigdal.com/privacidad.html">
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" type="image/svg+xml" href="icons/logo-icon.svg">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="theme-color" content="#211b13">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Rabino Yoel Migdal — Shiurim">
<meta property="og:title" content="${TITULO}">
<meta property="og:description" content="${DESCRIPCION}">
<meta property="og:url" content="https://yoelmigdal.com/privacidad.html">
<meta property="og:image" content="https://yoelmigdal.com/icons/icon-512.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root { --crema:#F7F3EA; --tinta:#211B13; --azul:#1C2B4A; --noche:#0B1428; --oro:#C79A4B; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--crema); color:var(--tinta); font-family:"Plus Jakarta Sans",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; line-height:1.65; -webkit-font-smoothing:antialiased; }
  a { color:var(--azul); }
  header.sitio { background:#fff; border-bottom:1px solid rgba(28,43,74,.1); }
  header.sitio .in { max-width:960px; margin:0 auto; padding:14px 20px; display:flex; align-items:center; justify-content:space-between; gap:12px; }
  header.sitio a.marca { display:flex; align-items:center; gap:10px; text-decoration:none; color:var(--tinta); font-family:"Playfair Display",Georgia,serif; font-size:19px; font-weight:600; line-height:1.15; }
  header.sitio img { width:40px; height:36px; }
  .boton { display:inline-flex; align-items:center; justify-content:center; min-height:44px; padding:0 22px; border-radius:999px; background:var(--azul); color:#fff; text-decoration:none; font-weight:600; font-size:14px; white-space:nowrap; }
  main { max-width:760px; margin:0 auto; padding:28px 20px 56px; }
  nav.migas { font-size:13px; color:#746850; margin-bottom:18px; }
  nav.migas a { color:#746850; }
  h1 { font-family:"Playfair Display",Georgia,serif; font-size:clamp(26px,5vw,38px); line-height:1.15; color:var(--azul); margin:6px 0 8px; font-weight:700; letter-spacing:-.01em; }
  h2 { font-family:"Playfair Display",Georgia,serif; color:var(--azul); font-size:22px; margin:34px 0 12px; }
  main p, main li { color:#332C21; }
  main ul { padding-left:22px; }
  main li { margin:4px 0; }
  footer.dedicatoria { background:var(--noche); text-align:center; padding:34px 20px 38px; }
  footer.dedicatoria i { display:block; width:64px; height:1px; margin:0 auto 18px; background:linear-gradient(90deg,transparent,var(--oro),transparent); }
  footer.dedicatoria p { margin:0; font-family:"Playfair Display",Georgia,serif; font-style:italic; color:rgba(244,231,198,.92); font-size:16px; letter-spacing:.02em; }
</style>
</head>
<body>
<header class="sitio"><div class="in">
  <a class="marca" href="./"><img src="icons/logo-ym.svg" alt="" width="40" height="36"><span>Rabino<br>Yoel Migdal</span></a>
  <a class="boton" href="./">Ver shiurim</a>
</div></header>
<main>
<nav class="migas"><a href="./">Inicio</a></nav>
<h1>Política de privacidad</h1>
${cuerpo}
</main>
<footer class="dedicatoria"><i></i><p>Leilui Nishmat Shaia ben Hersh wolf Z”L</p></footer>
</body>
</html>
`;
writeFileSync(new URL('../../privacidad.html', import.meta.url), html);
console.log('privacidad.html listo');
