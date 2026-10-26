// Compila la web para publicarla:
//   fuente/index.html  (el archivo que se edita: JSX + Tailwind por CDN, funciona solo con Babel)
//        ↓
//   index.html + app.js + styles.css  (lo que se publica: sin Babel ni Tailwind en el navegador)
//
// Uso:  cd tools && npm install && npm run build
// (hay que correrlo cada vez que se edita fuente/index.html)
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";

const aqui = dirname(fileURLToPath(import.meta.url));
const raiz = join(aqui, "..");
const fuente = readFileSync(join(raiz, "fuente", "index.html"), "utf8");

// 1) El componente React (JSX) → JavaScript común, minificado
const reBabel = /<script type="text\/babel">([\s\S]*?)<\/script>/;
const mBabel = fuente.match(reBabel);
if (!mBabel) throw new Error("No encontré el <script type=\"text/babel\"> en fuente/index.html");
// React y ReactDOM se empaquetan dentro de app.js (sin pedirlos a otro servidor).
const entrada0 = join(raiz, "tools", ".entrada.jsx");
writeFileSync(entrada0, `import * as React from "react";\nimport * as ReactDOM from "react-dom/client";\nimport PARASHOT from "./parashot.json";\n${mBabel[1]}`);
const resultado = buildSync({
  entryPoints: [entrada0],
  bundle: true,
  write: false,
  minify: true,
  format: "iife",
  target: "es2019",
  loader: { ".jsx": "jsx" },
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "none",
  absWorkingDir: join(raiz, "tools"),
});
rmSync(entrada0, { force: true });
const js = resultado.outputFiles[0].text;

// 2) La configuración de Tailwind (está inline en el HTML) → archivo para la herramienta
const reConfig = /<script>\s*tailwind\.config = ([\s\S]*?);\s*<\/script>/;
const mConfig = fuente.match(reConfig);
if (!mConfig) throw new Error("No encontré tailwind.config en fuente/index.html");
const tmp = mkdtempSync(join(tmpdir(), "tw-"));
const configPath = join(tmp, "tailwind.config.cjs");
writeFileSync(configPath, `module.exports = { content: [${JSON.stringify(join(raiz, "fuente", "index.html"))}], ...${mConfig[1]} };`);
const entrada = join(tmp, "in.css");
writeFileSync(entrada, "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n");
const salidaCss = join(tmp, "out.css");
execFileSync(join(aqui, "node_modules", ".bin", "tailwindcss"), ["-c", configPath, "-i", entrada, "-o", salidaCss, "--minify"], { stdio: "pipe" });
const css = readFileSync(salidaCss, "utf8");
rmSync(tmp, { recursive: true, force: true });

// 3) Archivos publicados
const corto = (t) => createHash("sha1").update(t).digest("hex").slice(0, 8);
writeFileSync(join(raiz, "app.js"), js);
writeFileSync(join(raiz, "styles.css"), css);

let html = fuente;
html = html.replace(reBabel, `<script src="app.js?v=${corto(js)}" defer></script>`);
html = html.replace(reConfig, "");
html = html.replace(
  /\s*<!-- Paleta: "stone"[\s\S]*?-->\s*(?=<style>)/,
  "\n\n"
);
html = html.replace(
  /<!-- Tailwind CSS \(via CDN[^>]*-->\s*<script src="https:\/\/cdn\.tailwindcss\.com"><\/script>/,
  `<!-- Estilos (Tailwind compilado de antemano) -->\n  <link rel="stylesheet" href="styles.css?v=${corto(css)}" />`
);
html = html.replace(/\s*<!-- Babel[^>]*-->\s*<script src="https:\/\/unpkg\.com\/@babel\/standalone[^>]*><\/script>/, "");
html = html.replace(/\s*<!-- React \+ ReactDOM[^>]*-->(\s*<script src="https:\/\/unpkg\.com\/react(?:-dom)?@18\.3\.1\/umd\/[^"]+"><\/script>)+/, "");
html = html.replace(/\s*<link rel="preconnect" href="https:\/\/cdn\.tailwindcss\.com"[^>]*>/, "");
html = html.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<!-- ARCHIVO GENERADO por tools/build.mjs a partir de fuente/index.html: no editar acá, editar fuente/index.html y volver a compilar. -->");

html = html.replace(/\s*<link rel="preconnect" href="https:\/\/unpkg\.com"[^>]*>/, "");
if (html.includes("unpkg.com")) throw new Error("Quedó una referencia a unpkg.com en el HTML compilado");
if (html.includes("cdn.tailwindcss.com") || html.includes("@babel/standalone") || html.includes("tailwind.config")) {
  const resto = html.split("\n").filter((l) => /cdn\.tailwindcss\.com|@babel\/standalone|tailwind\.config/.test(l));
  throw new Error("Quedaron referencias a Tailwind CDN o Babel en el HTML compilado:\n" + resto.join("\n"));
}
writeFileSync(join(raiz, "index.html"), html);
console.log(`Listo: app.js ${(js.length / 1024).toFixed(0)} KB, styles.css ${(css.length / 1024).toFixed(0)} KB, index.html ${(html.length / 1024).toFixed(0)} KB`);
