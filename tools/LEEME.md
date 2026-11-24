# Cómo se publica la web

La web se **compila antes de publicar** (así carga mucho más rápido que compilando en el navegador de cada visitante).

- **Se edita:** `fuente/index.html` (acá está todo el código: HTML, estilos y la aplicación React).
- **Se compila:** `cd tools && npm install` (una sola vez) y después `npm run build`.
- **Lo que se publica** (lo genera el comando, no se edita a mano): `index.html`, `app.js` y `styles.css`.

Después de compilar, subir los cambios a GitHub como siempre.

Qué hace el compilador (`tools/build.mjs`): convierte el código React a JavaScript común, genera solo los
estilos de Tailwind que se usan, y empaqueta React dentro de `app.js` (sin depender de servidores externos).

Los datos de los shiurim (`data.json`) y las páginas para buscadores (`s/`, `t/`, `sitemap.xml`) se siguen
generando solos con la sincronización de Spotify, no hay que compilar nada para eso.

## Parashá de la semana y fecha hebrea
- La barra de fecha y la sección "Parashá de la semana" usan `tools/parashot.json`, generado con Hebcal
  (`cd tools && node gen-parashot.mjs`). Cubre los Shabatot de 2025 a 2045 (Diáspora). Para ampliar el rango,
  cambiar `HASTA` en `gen-parashot.mjs` y volver a correrlo y compilar.
- El shiur de cada Parashá se busca solo: un shiur de la categoría "Parashá de la semana" cuyo título sea
  "N - Nombre - Parashá…". Si hubiera más de uno, se usa el más nuevo.
- Para forzar un shiur concreto, agregar en `data.json` → `config` un mapa `"parashaShiur": { "Vayera": 1786037186896 }`
  (nombre de la Parashá en inglés de Hebcal, o en español, y el id del shiur).

## Tania del Día
- **Audio:** se elige solo, del feed de Spotify: el episodio cuyo título lleva la fecha hebrea de hoy
  (por ejemplo "Tania 19 de Kislev"; también se entienden las letras hebreas, "י״ט כסלו"). Si todavía no se subió el de hoy,
  muestra el último anterior (hasta ~2 meses atrás) avisándolo. El día hebreo cambia a la puesta de sol de Buenos Aires.
  Estos audios no aparecen en "Últimos Shiurim" del inicio (tienen su sección), pero sí en el tema Tania y en las búsquedas.
- **Texto hebreo:** lo prepara `scripts/tania_del_dia.py` (corre solo en la sincronización diaria) desde Sefaria
  (texto de Kehot, licencia CC BY-NC: la web cita la fuente). Escribe `tania/AAAA-MM-DD.json` para ayer y 8 días adelante.
  `scripts/tania-he.json` es el texto completo del Tanya, guardado una sola vez. `python3 scripts/tania_del_dia.py --probar`
  revisa 400 días seguidos sin escribir nada.
- **Español:** la traducción es de Chabad.org y su página bloquea las consultas automáticas, así que la web enlaza
  a `es.chabad.org/dailystudy/tanya.asp?tdate=M/D/AAAA` (fecha sin ceros a la izquierda). Si Chabad autorizara el uso del texto
  (o ofreciera una API o widget), se puede agregar.
