// Service Worker de la web de shiurim del Rabino Yoel Migdal.
//
// Objetivo: permitir que la web se pueda "instalar" (PWA) y siga abriendo
// aunque no haya conexión, SIN afectar nunca la actualización de los
// shiurim. Por eso la regla más importante de este archivo es:
//
//   data.json NUNCA se guarda en caché ni se sirve desde caché acá.
//
// Si en algún momento se cambia este archivo, esa regla debe conservarse:
// de lo contrario, los visitantes podrían volver a ver una lista vieja de
// shiurim aunque se haya publicado una nueva.

// IMPORTANTE: cada vez que se sube una versión nueva de este archivo (aunque
// sea un cambio chico), conviene subir también el número de versión de acá
// abajo (v2, v3, ...). Eso invalida cualquier caché vieja que haya quedado
// de una versión anterior del Service Worker en el navegador de un visitante.
const CACHE_NAME = "ry-migdal-shiurim-v3";
const APP_SHELL = ["./", "./index.html", "./manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .catch(() => {
        // Si falla el pre-cacheo (por ejemplo, sin conexión al instalar),
        // no rompe nada: el service worker igual queda instalado y cachea
        // los archivos la primera vez que se pidan con éxito.
      })
  );
  // Hace que este Service Worker nuevo pase a estar "esperando" -> "activo"
  // de inmediato, sin esperar a que se cierren todas las pestañas viejas.
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((nombres) =>
        Promise.all(nombres.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
      )
      .then(() => self.clients.claim()) // toma control de las pestañas ya abiertas, sin esperar a que se recarguen
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Solo se maneja GET; todo lo demás (POST, etc.) pasa directo a la red.
  if (event.request.method !== "GET") return;

  // REGLA CRÍTICA — Estrategia "Network Only" para data.json:
  // nunca se lee ni se guarda en la Cache Storage del Service Worker. Se
  // reenvía la petición directo a la red, tal cual la armó index.html (que ya
  // viene con cache-buster y "no-store"). Así, ni el Service Worker ni la
  // caché HTTP del navegador pueden devolver una copia vieja de los shiurim.
  if (url.pathname.endsWith("data.json")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Los audios y portadas de los shiurim viven en otros servidores (Spotify,
  // CDNs de imágenes, etc.). Tampoco se cachean acá: se dejan pasar directo,
  // para no gastar espacio ni desactualizar contenido ajeno.
  if (url.origin !== self.location.origin) {
    return;
  }

  // Para los archivos propios de la web (index.html, manifest.json, este
  // mismo service worker): estrategia "Network First". Primero se intenta la
  // red, para tener siempre la versión más nueva publicada. Se usa
  // "cache: no-store" en el fetch a propósito: así se ignora por completo
  // cualquier copia guardada en la caché HTTP del navegador o de la CDN del
  // hosting (importante porque, a diferencia de Netlify, GitHub Pages y
  // Vercel no dejan configurar un archivo "_headers" con Cache-Control
  // personalizado — esta es la forma de lograr el mismo resultado sin
  // depender de esos headers). Solo si la red falla (sin conexión) se usa la
  // última copia guardada en caché, para que la web no quede en blanco.
  event.respondWith(
    fetch(event.request, { cache: "no-store" })
      .then((respuesta) => {
        const copia = respuesta.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copia));
        return respuesta;
      })
      .catch(() => caches.match(event.request))
  );
});
