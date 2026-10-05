# Contador de reproducciones

Servicio gratuito (Cloudflare Worker + base D1) que cuenta lo que se escucha en
la web y lo muestra en la sección **Popularidad del Panel Admin**. Spotify no
ofrece ninguna API con las reproducciones de un episodio, por eso se cuentan acá.
El inicio de la web NO usa estos números: sus "Destacados" se eligen a mano
(`config.destacados` en `data.json`).

- `POST /reproduccion` `{ "id": "<id del shiur>" }` suma 1 reproducción.
- `GET /conteos` devuelve las reproducciones de cada shiur (solo lo pide el Panel Admin).
- Solo se aceptan ids de shiurim que existen (se comprueba contra `s/<id>.html`).

## Cómo cuenta
- Una reproducción cuenta tras **30 segundos reales** de audio (la velocidad se
  tiene en cuenta; adelantar o retroceder no suma; escuchar como administrador
  tampoco).
- La misma persona suma **1 vez cada 6 horas por shiur**.
- **Privacidad:** no se guarda ninguna IP. Solo una huella (hash con clave
  secreta) de IP + shiur durante 6 horas, y después se borra sola.

## Publicarlo (una sola vez)
```bash
cd contador
npx wrangler login                              # abre el navegador: iniciar sesión en Cloudflare y "Allow"
npx wrangler d1 create shiurim-contador         # copiar el database_id en wrangler.toml
npx wrangler d1 execute shiurim-contador --remote --file=schema.sql
openssl rand -hex 16 | npx wrangler secret put SAL   # clave secreta para las huellas
npx wrangler deploy                             # devuelve la URL https://shiurim-contador.<cuenta>.workers.dev
```
Esa URL va en `CONTADOR_URL` dentro de `index.html`.

## Probarlo en la computadora (sin cuenta)
```bash
cd contador
npx wrangler d1 execute shiurim-contador --local --file=schema.sql
npx wrangler dev --local --port 8787
```

## Ver los números reales
```bash
npx wrangler d1 execute shiurim-contador --remote --command "SELECT * FROM reproducciones ORDER BY total DESC LIMIT 20"
```
