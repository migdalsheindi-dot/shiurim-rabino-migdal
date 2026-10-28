// Contador de reproducciones de la web de shiurim (Cloudflare Worker + D1).
//
//   POST /reproduccion  { "id": "<id del shiur>" }  -> suma 1 reproducción
//   GET  /conteos                                    -> reproducciones de cada shiur
//
//   POST /visita        { pagina }                       -> suma una visita (y un único si es la 1ª del día)
//   POST /escucha       { id, segundos }                 -> suma segundos escuchados de un shiur
//   POST /evento        { tipo, origen, contexto }       -> clics de donación
//   POST /suscribir     { nombre, apellido, email }      -> anota a alguien para recibir novedades
//   GET  /suscriptores  (con clave secreta)              -> lista de suscriptores, para el Panel Admin
//   GET  /estadisticas?dias=30   (con clave secreta)     -> todo lo anterior resumido, para el Panel Admin
//
// Lo usa el Panel Admin para mostrar la popularidad real de cada shiur y el
// tráfico de la web.
//
// País de los visitantes: lo informa Cloudflare en cada pedido (request.cf.country),
// sin servicios externos y sin guardar la IP; solo se suma 1 al contador del país.
//
// Privacidad: no se guarda ninguna IP ni se usan cookies. Para no contar dos
// veces a la misma persona se guarda una huella (hash con clave secreta) de
// IP + navegador + día (se borra a los 2 días) y, para las reproducciones, de
// IP + shiur durante 6 horas. Todo lo demás son contadores por día
// (incluido el país). La única excepción son los datos que una persona escribe a propósito
// en el formulario de Suscripción (nombre, apellido y email).
//
// Las estadísticas solo se leen con la clave secreta ADMIN_TOKEN (un "secret"
// del Worker, que no está en ningún archivo del sitio).

const ORIGENES_PERMITIDOS = [
  "https://yoelmigdal.com",
  "https://www.yoelmigdal.com",
  "https://migdalsheindi-dot.github.io",
  "capacitor://localhost", // app de iPhone (Capacitor)
  "https://localhost", // app de Android (Capacitor)
  "http://localhost:8123", // pruebas locales
];

// Cada shiur publicado tiene una página s/<id>.html (la de compartir). Sirve
// para comprobar que el id existe y que nadie inventa ids para llenar la base.
const PAGINAS_DE_SHIURIM = "https://yoelmigdal.com/s/";

const TIPOS_EVENTO = ["donar_abrir", "donar_click"];
const ORIGENES_EVENTO = ["encabezado", "menu", "modal"];
const MAX_SEGUNDOS_POR_ENVIO = 900;
const ZONA_HORARIA_MS = -3 * 60 * 60 * 1000; // Argentina (UTC-3)

// Día de hoy (AAAA-MM-DD) en hora de Argentina, o el de hace n días
function hoy(restarDias = 0) {
  return new Date(Date.now() + ZONA_HORARIA_MS - restarDias * 86400000).toISOString().slice(0, 10);
}

// Páginas válidas: inicio, busqueda, tema:<nombre> o shiur:<id>
function paginaValida(p) {
  return typeof p === "string" && (p === "inicio" || p === "busqueda" || /^shiur:\d{1,20}$/.test(p) || /^tema:[\p{L} ]{1,40}$/u.test(p));
}

function esMobile(request) {
  return /Mobi|Android|iPhone|iPad|iPod/i.test(request.headers.get("User-Agent") || "");
}

function paisDe(request) {
  const p = request.cf && request.cf.country;
  return typeof p === "string" && /^[A-Z]{2}$/.test(p) ? p : "XX"; // XX = desconocido
}

const MAX_SUSCRIPTORES = 20000;
const ESPERA_ENTRE_ALTAS_MS = 30 * 1000; // una misma persona puede anotarse 1 vez cada 30 s
const RE_EMAIL = /^[^\s@]{1,64}@[^\s@]{1,255}\.[^\s@.]{2,}$/;

function limpiarTexto(v, max) {
  return typeof v === "string" ? v.replace(/[\u0000-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim().slice(0, max) : "";
}

function claveCorrecta(request, env) {
  const esperado = env.ADMIN_TOKEN || "";
  const recibido = (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  if (!esperado || recibido.length !== esperado.length) return false;
  let diferencia = 0; // comparación en tiempo constante
  for (let i = 0; i < esperado.length; i++) diferencia |= esperado.charCodeAt(i) ^ recibido.charCodeAt(i);
  return diferencia === 0;
}

const VENTANA_MS = 6 * 60 * 60 * 1000; // una misma persona cuenta 1 vez cada 6 h por shiur
const MAX_SHIURIM_EN_RESPUESTA = 1000;

function cabecerasCors(request) {
  const origen = request.headers.get("Origin");
  return {
    "Access-Control-Allow-Origin": ORIGENES_PERMITIDOS.includes(origen) ? origen : ORIGENES_PERMITIDOS[0],
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(datos, estado, cabeceras) {
  return new Response(JSON.stringify(datos), {
    status: estado,
    headers: { "Content-Type": "application/json; charset=utf-8", ...cabeceras },
  });
}

async function leerCuerpo(request) {
  try {
    return await request.json();
  } catch (e) {
    return null;
  }
}

async function huella(texto) {
  const bytes = new TextEncoder().encode(texto);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, "0")).join("");
}

// true = existe, false = no existe, null = no se pudo comprobar
async function existeElShiur(id, env) {
  const base = env.PAGINAS_DE_SHIURIM || PAGINAS_DE_SHIURIM;
  try {
    const r = await fetch(`${base}${id}.html`, {
      method: "HEAD",
      cf: { cacheEverything: true, cacheTtl: 3600 },
    });
    if (r.status === 200) return true;
    if (r.status === 404) return false;
    return null;
  } catch (e) {
    return null;
  }
}

// ---- Aviso automático a GitHub cuando hay novedades en el feed de Spotify ----------
// GitHub ejecuta sus tareas programadas "cuando puede" (a veces con horas de demora).
// Este Worker mira el feed cada minuto y, apenas cambia (episodio nuevo, título o
// portada editados en Spotify Creators), le pide a GitHub que sincronice YA.
// Necesita el secret GITHUB_TOKEN (una clave de GitHub con permiso solo para lanzar
// el workflow de este repositorio); sin ella no hace nada.
const FEED_URL = "https://anchor.fm/s/2fd6a950/podcast/rss";
const MIN_ENTRE_AVISOS_MS = 3 * 60 * 1000;

async function revisarFeed(env) {
  if (!env.GITHUB_TOKEN) return { ok: false, motivo: "falta GITHUB_TOKEN" };
  const repo = env.GITHUB_REPO || "migdalsheindi-dot/shiurim-rabino-migdal";
  const r = await fetch(`${FEED_URL}?cb=${Math.floor(Date.now() / 60000)}`, {
    headers: { "Cache-Control": "no-cache", Pragma: "no-cache", "User-Agent": "Mozilla/5.0 (compatible; ShiurimAviso/1.0)" },
    cf: { cacheTtl: 0, cacheEverything: false },
  });
  if (!r.ok) return { ok: false, motivo: `feed HTTP ${r.status}` };
  const xml = await r.text();
  const fecha = (xml.match(/<lastBuildDate>([^<]*)<\/lastBuildDate>/) || [])[1] || "";
  const episodios = (xml.match(/<item>/g) || []).length;
  if (!fecha) return { ok: false, motivo: "el feed no trae lastBuildDate" };
  const huella = `${fecha}|${episodios}`;

  const previo = await env.DB.prepare("SELECT valor FROM estado WHERE clave = 'feed'").first();
  const aviso = await env.DB.prepare("SELECT valor FROM estado WHERE clave = 'ultimo_aviso'").first();
  if (previo && previo.valor === huella) return { ok: true, motivo: "sin cambios" };
  if (aviso && Date.now() - Number(aviso.valor) < MIN_ENTRE_AVISOS_MS) return { ok: true, motivo: "aviso reciente, se espera" };

  const g = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/sync-spotify.yml/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "shiurim-aviso",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ref: "main" }),
  });
  if (g.status !== 204) return { ok: false, motivo: `GitHub respondió ${g.status}` };
  await env.DB.batch([
    env.DB.prepare("INSERT INTO estado (clave, valor) VALUES ('feed', ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor").bind(huella),
    env.DB.prepare("INSERT INTO estado (clave, valor) VALUES ('ultimo_aviso', ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor").bind(String(Date.now())),
  ]);
  return { ok: true, motivo: `GitHub avisado (${huella})` };
}

// ---- Avisos de shiurim nuevos en la app (Firebase Cloud Messaging) -------------------
// Cada minuto mira el episodio más nuevo del feed. Cuando aparece uno distinto al último
// avisado Y ya está publicado en la web (data-lite.json), manda UN aviso al tema "shiurim"
// de Firebase: le llega a todos los teléfonos que activaron los avisos en la app.
// Necesita el secret FCM_CUENTA (el JSON de la "cuenta de servicio" de Firebase); sin él no hace nada.
const TEMA_AVISOS = "shiurim";
const DATOS_WEB = "https://yoelmigdal.com/data-lite.json";

function base64url(bytes) {
  let s = "";
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// Permiso de Google para mandar avisos: un JWT firmado con la clave de la cuenta de servicio
async function tokenDeFirebase(cuenta) {
  const ahora = Math.floor(Date.now() / 1000);
  const enc = new TextEncoder();
  const cabecera = base64url(enc.encode(JSON.stringify({ alg: "RS256", typ: "JWT" })));
  const datos = base64url(enc.encode(JSON.stringify({
    iss: cuenta.client_email,
    scope: "https://www.googleapis.com/auth/firebase.messaging",
    aud: "https://oauth2.googleapis.com/token",
    iat: ahora,
    exp: ahora + 3600,
  })));
  const pem = cuenta.private_key.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  const clave = await crypto.subtle.importKey(
    "pkcs8",
    Uint8Array.from(atob(pem), (c) => c.charCodeAt(0)),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const firma = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", clave, enc.encode(`${cabecera}.${datos}`));
  const r = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=${cabecera}.${datos}.${base64url(firma)}`,
  });
  if (!r.ok) throw new Error(`Google respondió ${r.status} al pedir permiso`);
  return (await r.json()).access_token;
}

function decodificarXml(t) {
  return String(t || "")
    .replace(/^<!\[CDATA\[|\]\]>$/g, "")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .trim();
}

async function avisarShiurNuevo(env) {
  if (!env.FCM_CUENTA) return { ok: false, motivo: "falta FCM_CUENTA" };
  const r = await fetch(`${FEED_URL}?cb=${Math.floor(Date.now() / 60000)}`, { headers: { "User-Agent": "Mozilla/5.0 (compatible; ShiurimAviso/1.0)" } });
  if (!r.ok) return { ok: false, motivo: `feed HTTP ${r.status}` };
  const item = ((await r.text()).match(/<item>([\s\S]*?)<\/item>/) || [])[1];
  if (!item) return { ok: false, motivo: "feed sin episodios" };
  const audio = (item.match(/<enclosure[^>]*url="([^"]+)"/) || [])[1];
  const titulo = decodificarXml((item.match(/<title>([\s\S]*?)<\/title>/) || [])[1]);
  if (!audio) return { ok: false, motivo: "episodio sin audio" };

  const previo = await env.DB.prepare("SELECT valor FROM estado WHERE clave = 'aviso_push'").first();
  const guardar = () => env.DB.prepare("INSERT INTO estado (clave, valor) VALUES ('aviso_push', ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor").bind(audio).run();
  if (!previo) { await guardar(); return { ok: true, motivo: "primer registro, sin aviso" }; }
  if (previo.valor === audio) return { ok: true, motivo: "sin cambios" };

  // Espera a que la web ya lo tenga, así al tocar el aviso el shiur aparece en la app
  const datos = await fetch(`${DATOS_WEB}?cb=${Date.now()}`, { cf: { cacheTtl: 0 } }).then((x) => (x.ok ? x.json() : null)).catch(() => null);
  if (!datos || !Array.isArray(datos.shiurim) || !datos.shiurim.some((s) => s.audioUrl === audio)) {
    return { ok: true, motivo: "esperando que la web publique el episodio" };
  }

  const cuenta = JSON.parse(env.FCM_CUENTA);
  const token = await tokenDeFirebase(cuenta);
  const envio = await fetch(`https://fcm.googleapis.com/v1/projects/${cuenta.project_id}/messages:send`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      message: {
        topic: TEMA_AVISOS,
        notification: { title: "Nuevo shiur del Rabino Yoel Migdal", body: titulo.slice(0, 180) },
        android: { priority: "HIGH", notification: { channel_id: "shiurim", icon: "ic_notificacion", color: "#211B13" } },
      },
    }),
  });
  if (!envio.ok) return { ok: false, motivo: `Firebase respondió ${envio.status}: ${(await envio.text()).slice(0, 200)}` };
  await guardar();
  return { ok: true, motivo: `aviso enviado: ${titulo}` };
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      revisarFeed(env)
        .then((r) => { if (!r.ok || r.motivo !== "sin cambios") console.log("revisión del feed:", JSON.stringify(r)); })
        .catch((e) => console.log("error revisando el feed:", String(e)))
    );
    ctx.waitUntil(
      avisarShiurNuevo(env)
        .then((r) => { if (!r.ok || !["sin cambios", "falta FCM_CUENTA"].includes(r.motivo)) console.log("avisos:", JSON.stringify(r)); })
        .catch((e) => console.log("error en avisos:", String(e)))
    );
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = cabecerasCors(request);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });

    if (url.pathname === "/conteos" && request.method === "GET") {
      const { results } = await env.DB.prepare(
        "SELECT shiur_id, total FROM reproducciones WHERE total > 0 ORDER BY total DESC LIMIT ?"
      )
        .bind(MAX_SHIURIM_EN_RESPUESTA)
        .all();
      const conteos = {};
      for (const fila of results) conteos[fila.shiur_id] = fila.total;
      return json({ conteos }, 200, { ...cors, "Cache-Control": "no-cache" });
    }

    if (url.pathname === "/reproduccion" && request.method === "POST") {
      if (!ORIGENES_PERMITIDOS.includes(request.headers.get("Origin"))) {
        return json({ error: "origen no permitido" }, 403, cors);
      }
      let cuerpo;
      try {
        cuerpo = await request.json();
      } catch (e) {
        return json({ error: "JSON inválido" }, 400, cors);
      }
      const id = String(cuerpo && cuerpo.id !== undefined ? cuerpo.id : "");
      if (!/^\d{1,20}$/.test(id)) return json({ error: "id inválido" }, 400, cors);

      const existe = await existeElShiur(id, env);
      if (existe === false) return json({ error: "shiur desconocido" }, 404, cors);
      if (existe === null) return json({ error: "no se pudo comprobar el shiur" }, 503, cors);

      const ip = request.headers.get("CF-Connecting-IP") || "";
      const clave = await huella(`${ip}|${id}|${env.SAL || "sin-sal"}`);
      const ahora = Date.now();

      const previo = await env.DB.prepare("SELECT ts FROM oyentes WHERE huella = ?").bind(clave).first();
      if (previo && ahora - previo.ts < VENTANA_MS) return json({ contado: false }, 200, cors);

      await env.DB.batch([
        env.DB.prepare(
          "INSERT INTO oyentes (huella, ts) VALUES (?, ?) ON CONFLICT(huella) DO UPDATE SET ts = excluded.ts"
        ).bind(clave, ahora),
        env.DB.prepare(
          "INSERT INTO reproducciones (shiur_id, total) VALUES (?, 1) ON CONFLICT(shiur_id) DO UPDATE SET total = total + 1"
        ).bind(id),
        env.DB.prepare("DELETE FROM oyentes WHERE ts < ?").bind(ahora - VENTANA_MS),
        env.DB.prepare(
          `INSERT INTO escucha_dia (dia, shiur_id, reproducciones, segundos) VALUES (?, ?, 1, 0)
           ON CONFLICT(dia, shiur_id) DO UPDATE SET reproducciones = reproducciones + 1`
        ).bind(hoy(), id),
      ]);
      return json({ contado: true }, 200, cors);
    }

    // ---- Estadísticas ----------------------------------------------------
    const permitidoPost = ORIGENES_PERMITIDOS.includes(request.headers.get("Origin"));

    if (url.pathname === "/visita" && request.method === "POST") {
      if (!permitidoPost) return json({ error: "origen no permitido" }, 403, cors);
      const cuerpo = await leerCuerpo(request);
      if (!cuerpo || !paginaValida(cuerpo.pagina)) return json({ error: "página inválida" }, 400, cors);
      const dia = hoy();
      const ip = request.headers.get("CF-Connecting-IP") || "";
      const ua = request.headers.get("User-Agent") || "";
      const clave = await huella(`${ip}|${ua}|${dia}|${env.SAL || "sin-sal"}`);
      const nuevo = await env.DB.prepare("INSERT OR IGNORE INTO visitantes (dia, huella) VALUES (?, ?)").bind(dia, clave).run();
      const esUnico = nuevo.meta && nuevo.meta.changes > 0 ? 1 : 0;
      const movil = esMobile(request) ? 1 : 0;
      await env.DB.batch([
        env.DB.prepare(
          `INSERT INTO dias (dia, visitas, unicos, mobile, desktop) VALUES (?, 1, ?, ?, ?)
           ON CONFLICT(dia) DO UPDATE SET visitas = visitas + 1, unicos = unicos + ?, mobile = mobile + ?, desktop = desktop + ?`
        ).bind(dia, esUnico, movil, 1 - movil, esUnico, movil, 1 - movil),
        env.DB.prepare(
          "INSERT INTO paginas (dia, pagina, total) VALUES (?, ?, 1) ON CONFLICT(dia, pagina) DO UPDATE SET total = total + 1"
        ).bind(dia, cuerpo.pagina),
        env.DB.prepare(
          `INSERT INTO paises (dia, pais, visitas, unicos) VALUES (?, ?, 1, ?)
           ON CONFLICT(dia, pais) DO UPDATE SET visitas = visitas + 1, unicos = unicos + ?`
        ).bind(dia, paisDe(request), esUnico, esUnico),
        env.DB.prepare("DELETE FROM visitantes WHERE dia < ?").bind(hoy(2)),
      ]);
      return json({ ok: true }, 200, cors);
    }

    if (url.pathname === "/suscribir" && request.method === "POST") {
      if (!permitidoPost) return json({ error: "origen no permitido" }, 403, cors);
      const cuerpo = await leerCuerpo(request);
      if (!cuerpo) return json({ error: "datos inválidos" }, 400, cors);
      if (cuerpo.web) return json({ ok: true }, 200, cors); // campo trampa para robots: se ignora en silencio
      const nombre = limpiarTexto(cuerpo.nombre, 60);
      const apellido = limpiarTexto(cuerpo.apellido, 60);
      const email = limpiarTexto(cuerpo.email, 150).toLowerCase();
      if (!nombre || !apellido || !RE_EMAIL.test(email)) return json({ error: "datos inválidos" }, 400, cors);

      const ip = request.headers.get("CF-Connecting-IP") || "";
      const clave = await huella(`alta|${ip}|${env.SAL || "sin-sal"}`);
      const ahora = Date.now();
      const previo = await env.DB.prepare("SELECT ts FROM oyentes WHERE huella = ?").bind(clave).first();
      if (previo && ahora - previo.ts < ESPERA_ENTRE_ALTAS_MS) return json({ error: "demasiados intentos" }, 429, cors);
      const { total } = await env.DB.prepare("SELECT COUNT(*) AS total FROM suscriptores").first();
      if (total >= MAX_SUSCRIPTORES) return json({ error: "lista completa" }, 503, cors);

      await env.DB.batch([
        env.DB.prepare("INSERT INTO oyentes (huella, ts) VALUES (?, ?) ON CONFLICT(huella) DO UPDATE SET ts = excluded.ts").bind(clave, ahora),
        env.DB.prepare("DELETE FROM oyentes WHERE ts < ?").bind(ahora - VENTANA_MS),
        // Si el email ya estaba, no se duplica (y no se avisa si existía o no)
        env.DB.prepare("INSERT OR IGNORE INTO suscriptores (email, nombre, apellido, fecha) VALUES (?, ?, ?, ?)").bind(email, nombre, apellido, new Date().toISOString()),
      ]);
      return json({ ok: true }, 200, cors);
    }

    if (url.pathname === "/escucha" && request.method === "POST") {
      if (!permitidoPost) return json({ error: "origen no permitido" }, 403, cors);
      const cuerpo = await leerCuerpo(request);
      const id = String(cuerpo && cuerpo.id !== undefined ? cuerpo.id : "");
      const segundos = Math.round(Number(cuerpo && cuerpo.segundos));
      if (!/^\d{1,20}$/.test(id) || !(segundos >= 1 && segundos <= MAX_SEGUNDOS_POR_ENVIO)) return json({ error: "datos inválidos" }, 400, cors);
      if ((await existeElShiur(id, env)) === false) return json({ error: "shiur desconocido" }, 404, cors);
      await env.DB.prepare(
        `INSERT INTO escucha_dia (dia, shiur_id, reproducciones, segundos) VALUES (?, ?, 0, ?)
         ON CONFLICT(dia, shiur_id) DO UPDATE SET segundos = segundos + ?`
      ).bind(hoy(), id, segundos, segundos).run();
      return json({ ok: true }, 200, cors);
    }

    if (url.pathname === "/evento" && request.method === "POST") {
      if (!permitidoPost) return json({ error: "origen no permitido" }, 403, cors);
      const cuerpo = await leerCuerpo(request);
      if (!cuerpo || !TIPOS_EVENTO.includes(cuerpo.tipo) || !ORIGENES_EVENTO.includes(cuerpo.origen) || !paginaValida(cuerpo.contexto)) {
        return json({ error: "evento inválido" }, 400, cors);
      }
      await env.DB.prepare(
        `INSERT INTO eventos (dia, tipo, origen, contexto, total) VALUES (?, ?, ?, ?, 1)
         ON CONFLICT(dia, tipo, origen, contexto) DO UPDATE SET total = total + 1`
      ).bind(hoy(), cuerpo.tipo, cuerpo.origen, cuerpo.contexto).run();
      return json({ ok: true }, 200, cors);
    }

    if (url.pathname === "/estadisticas" && request.method === "GET") {
      if (!env.ADMIN_TOKEN) return json({ error: "estadísticas sin configurar" }, 503, cors);
      if (!claveCorrecta(request, env)) return json({ error: "clave incorrecta" }, 401, cors);
      const dias = Math.min(365, Math.max(1, parseInt(url.searchParams.get("dias"), 10) || 30));
      const desde = hoy(dias - 1);
      const [porDia, paginas, shiurim, donaciones, paises, subs, subsNuevos] = await Promise.all([
        env.DB.prepare("SELECT dia, visitas, unicos, mobile, desktop FROM dias WHERE dia >= ? ORDER BY dia").bind(desde).all(),
        env.DB.prepare("SELECT pagina, SUM(total) AS total FROM paginas WHERE dia >= ? GROUP BY pagina ORDER BY total DESC LIMIT 25").bind(desde).all(),
        env.DB.prepare(
          "SELECT shiur_id AS id, SUM(reproducciones) AS reproducciones, SUM(segundos) AS segundos FROM escucha_dia WHERE dia >= ? GROUP BY shiur_id ORDER BY reproducciones DESC, segundos DESC LIMIT 30"
        ).bind(desde).all(),
        env.DB.prepare("SELECT tipo, origen, contexto, SUM(total) AS total FROM eventos WHERE dia >= ? GROUP BY tipo, origen, contexto ORDER BY total DESC LIMIT 60").bind(desde).all(),
        env.DB.prepare("SELECT pais, SUM(visitas) AS visitas, SUM(unicos) AS unicos FROM paises WHERE dia >= ? GROUP BY pais ORDER BY visitas DESC LIMIT 40").bind(desde).all(),
        env.DB.prepare("SELECT COUNT(*) AS total FROM suscriptores").first(),
        env.DB.prepare("SELECT COUNT(*) AS total FROM suscriptores WHERE fecha >= ?").bind(`${desde}T00:00:00`).first(),
      ]);
      return json(
        {
          desde, hasta: hoy(), dias: porDia.results, paginas: paginas.results, shiurim: shiurim.results,
          donaciones: donaciones.results, paises: paises.results, suscriptores: { total: subs.total, nuevos: subsNuevos.total },
        },
        200,
        { ...cors, "Cache-Control": "no-store" }
      );
    }

    if (url.pathname === "/suscriptores" && request.method === "GET") {
      if (!env.ADMIN_TOKEN) return json({ error: "estadísticas sin configurar" }, 503, cors);
      if (!claveCorrecta(request, env)) return json({ error: "clave incorrecta" }, 401, cors);
      const { results } = await env.DB.prepare("SELECT nombre, apellido, email, fecha FROM suscriptores ORDER BY fecha DESC LIMIT ?").bind(MAX_SUSCRIPTORES).all();
      return json({ suscriptores: results }, 200, { ...cors, "Cache-Control": "no-store" });
    }

    return json({ error: "no encontrado" }, 404, cors);
  },
};
