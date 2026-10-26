// Arma movil/www con lo que la app lleva adentro: la web ya compilada (index.html, app.js, styles.css)
// y las imágenes fijas. Los datos (shiurim, transcripciones, miniaturas) NO se copian: la app los lee de
// yoelmigdal.com, así los shiurim nuevos aparecen sin publicar una versión nueva en las tiendas.
//
// Antes hay que compilar la web:  cd ../tools && npm run build
import { cpSync, rmSync, mkdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const raiz = join(aqui, "..");
const www = join(aqui, "www");

rmSync(www, { recursive: true, force: true });
mkdirSync(www);
for (const f of ["index.html", "app.js", "styles.css"]) {
  if (!existsSync(join(raiz, f))) throw new Error(`Falta ${f}: compilá la web primero (cd tools && npm run build)`);
  cpSync(join(raiz, f), join(www, f));
}
for (const d of ["icons", "img"]) cpSync(join(raiz, d), join(www, d), { recursive: true });
console.log("movil/www listo");
