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
