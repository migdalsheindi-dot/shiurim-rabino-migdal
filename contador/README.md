# Contador y estadísticas

Servicio gratuito (Cloudflare Worker + base D1) que junta, **sin cookies y sin guardar IPs**, lo que
pasa en la web y lo muestra en el **Panel de Estadísticas** del Panel Admin (botón "Ver estadísticas",
o el ícono de gráfico arriba a la derecha cuando estás como administrador).

Qué registra:
- **Visitas** por día, **visitantes únicos**, celular vs. computadora y **páginas más vistas**.
- **Reproducciones** de cada shiur (cuentan tras 30 s reales de audio) y **tiempo escuchado**.
- **Donaciones**: cuántos abrieron el aviso y cuántos tocaron "Donar con Mercado Pago", desde qué botón
  (encabezado, menú o aviso) y en qué parte de la web estaban. El monto lo elige cada persona dentro de
  Mercado Pago, por eso no se puede registrar acá.

No se registra nada de lo que hagas vos como administrador, ni de quienes tienen activado "No rastrear".

## Endpoints
- `POST /visita` `{ "pagina": "inicio" | "busqueda" | "tema:<nombre>" | "shiur:<id>" }`
- `POST /reproduccion` `{ "id": "<id>" }` suma 1 reproducción (1 vez cada 6 h por persona y shiur).
- `POST /escucha` `{ "id": "<id>", "segundos": 120 }` suma tiempo escuchado.
- `POST /evento` `{ "tipo": "donar_abrir" | "donar_click", "origen": "encabezado" | "menu" | "modal", "contexto": "<página>" }`
- `GET /conteos` reproducciones por shiur (público, lo usa la sección "Popularidad").
- `GET /estadisticas?dias=30` **solo con la clave secreta** (`Authorization: Bearer <ADMIN_TOKEN>`).
- Solo se aceptan pedidos que vengan de yoelmigdal.com, y solo ids de shiurim que existen.

## Privacidad
Solo se guarda una huella (hash con clave secreta) de IP + navegador + día, que se borra a los 2 días, y
una de IP + shiur durante 6 horas para no contar dos veces la misma escucha. Todo lo demás son contadores
por día. Las estadísticas se leen únicamente con `ADMIN_TOKEN`, una clave que existe solo dentro de
Cloudflare y que escribís vos en el panel (no está en ningún archivo del sitio).

## Publicarlo (una sola vez)
```bash
cd contador
npx wrangler login                              # abre el navegador: iniciar sesión en Cloudflare y "Allow"
npx wrangler d1 create shiurim-contador         # copiar el database_id en wrangler.toml
npx wrangler d1 execute shiurim-contador --remote --file=schema.sql
openssl rand -hex 16 | npx wrangler secret put SAL          # clave para las huellas
openssl rand -hex 16 | tee /dev/stderr | npx wrangler secret put ADMIN_TOKEN   # clave de las estadísticas: ANOTALA, sale en pantalla
npx wrangler deploy                             # devuelve la URL https://shiurim-contador.<cuenta>.workers.dev
```
Esa URL va en `CONTADOR_URL` dentro de `index.html`. Para ver las estadísticas: entrar como administrador →
"Ver estadísticas" → pegar la clave `ADMIN_TOKEN`.

Si ya tenías publicado el contador anterior, alcanza con volver a correr `schema.sql` (agrega las tablas
nuevas sin tocar las viejas), crear el secret `ADMIN_TOKEN` y `npx wrangler deploy`.

## Probarlo en la computadora (sin cuenta)
Crear `contador/.dev.vars` (no se sube a Git) con:
```
SAL=cualquier-texto
ADMIN_TOKEN=clave-de-prueba
PAGINAS_DE_SHIURIM=http://localhost:8123/s/
```
```bash
cd contador
npx wrangler d1 execute shiurim-contador --local --file=schema.sql
npx wrangler dev --local --port 8787
```

## Ver los números a mano
```bash
npx wrangler d1 execute shiurim-contador --remote --command "SELECT * FROM dias ORDER BY dia DESC LIMIT 14"
```
