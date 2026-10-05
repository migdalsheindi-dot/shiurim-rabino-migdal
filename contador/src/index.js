// Contador de reproducciones de la web de shiurim (Cloudflare Worker + D1).
//
//   POST /reproduccion  { "id": "<id del shiur>" }  -> suma 1 reproducción
//   GET  /conteos                                    -> reproducciones de cada shiur
//
// Lo usa el Panel Admin para mostrar la popularidad real de cada shiur.
//
// Privacidad: no se guarda ninguna IP. Para no contar dos veces a la misma
// persona se guarda, por 6 horas, una huella (hash con clave secreta) de
// IP + shiur, y después se borra sola.

const ORIGENES_PERMITIDOS = [
  "https://yoelmigdal.com",
  "https://www.yoelmigdal.com",
  "https://migdalsheindi-dot.github.io",
  "http://localhost:8123", // pruebas locales
];

// Cada shiur publicado tiene una página s/<id>.html (la de compartir). Sirve
// para comprobar que el id existe y que nadie inventa ids para llenar la base.
const PAGINAS_DE_SHIURIM = "https://yoelmigdal.com/s/";

const VENTANA_MS = 6 * 60 * 60 * 1000; // una misma persona cuenta 1 vez cada 6 h por shiur
const MAX_SHIURIM_EN_RESPUESTA = 1000;

function cabecerasCors(request) {
  const origen = request.headers.get("Origin");
  return {
    "Access-Control-Allow-Origin": ORIGENES_PERMITIDOS.includes(origen) ? origen : ORIGENES_PERMITIDOS[0],
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
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

export default {
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
      ]);
      return json({ contado: true }, 200, cors);
    }

    return json({ error: "no encontrado" }, 404, cors);
  },
};
