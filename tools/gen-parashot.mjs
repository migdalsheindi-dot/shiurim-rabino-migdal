// Genera tools/parashot.json: la Parashá (de la Diáspora) de cada Shabat de 2025 a 2045, con su
// nombre en español y hebreo y el pasaje de la Torá. Usa Hebcal (el calendario hebreo de referencia).
// Se corre a mano cuando haga falta ampliar el rango:  cd tools && node gen-parashot.mjs
import { writeFileSync } from "node:fs";
import { HDate, Sedra, HebrewCalendar, Locale, parshiot } from "@hebcal/core";
import { getLeyningForParsha } from "@hebcal/leyning";

const DESDE = new Date(2025, 0, 4); // primer sábado de 2025
const HASTA = new Date(2046, 0, 1);

// nombre Hebcal -> [nombre en español (como en los títulos de los shiurim), variantes de escritura]
const ES = {
  "Bereshit": ["Bereshit", ["bereshit", "bereshis", "bereshith"]],
  "Noach": ["Noaj", ["noaj", "noach", "noah"]],
  "Lech-Lecha": ["Lej Lejá", ["lej leja", "lech lecha", "lech-lecha", "lej-leja", "lekh lekha"]],
  "Vayera": ["Vaierá", ["vaiera", "vayera", "vayeira"]],
  "Chayei Sara": ["Jaie Sará", ["jaie sara", "jayei sara", "chayei sara", "jaiei sara", "hayei sara"]],
  "Toldot": ["Toldot", ["toldot", "toledot", "toldos"]],
  "Vayetzei": ["Vaietzé", ["vaietze", "vayetze", "vayetzei", "vaietzei"]],
  "Vayishlach": ["Vaishlaj", ["vaishlaj", "vayishlaj", "vayishlach", "vaishlach"]],
  "Vayeshev": ["Vaieshev", ["vaieshev", "vayeshev"]],
  "Miketz": ["Miketz", ["miketz", "mikets", "mikeitz"]],
  "Vayigash": ["Vaigash", ["vaigash", "vayigash"]],
  "Vayechi": ["Vaieji", ["vaieji", "vayechi", "vayeji", "vayehi"]],
  "Shemot": ["Shemot", ["shemot", "shemos", "sh'mot"]],
  "Vaera": ["Vaerá", ["vaera", "vaerá"]],
  "Bo": ["Bo", ["bo"]],
  "Beshalach": ["Beshalaj", ["beshalaj", "beshalach", "bishalaj"]],
  "Yitro": ["Itró", ["itro", "yitro", "jetro", "yitró"]],
  "Mishpatim": ["Mishpatim", ["mishpatim"]],
  "Terumah": ["Terumá", ["teruma", "terumah"]],
  "Tetzaveh": ["Tetzavé", ["tetzave", "tetzaveh", "tetsave"]],
  "Ki Tisa": ["Ki Tisá", ["ki tisa", "ki tissa", "ki-tisa"]],
  "Vayakhel": ["Vaiakhel", ["vaiakhel", "vayakhel", "vayakel", "vaiakel"]],
  "Pekudei": ["Pekudei", ["pekudei", "pekudey"]],
  "Vayikra": ["Vaikrá", ["vaikra", "vayikra"]],
  "Tzav": ["Tzav", ["tzav", "tsav"]],
  "Shmini": ["Shemini", ["shemini", "shmini"]],
  "Tazria": ["Tazría", ["tazria", "tazría"]],
  "Metzora": ["Metzorá", ["metzora", "metsora"]],
  "Achrei Mot": ["Ajarei Mot", ["ajarei mot", "acharei mot", "ajare mot", "ajaremot"]],
  "Kedoshim": ["Kedoshim", ["kedoshim", "kedoshím"]],
  "Emor": ["Emor", ["emor"]],
  "Behar": ["Behar", ["behar"]],
  "Bechukotai": ["Bejukotai", ["bejukotai", "bechukotai", "bejukotay"]],
  "Bamidbar": ["Bamidbar", ["bamidbar"]],
  "Nasso": ["Nasó", ["naso", "nasso"]],
  "Beha'alotcha": ["Behaalotjá", ["behaalotja", "behaalotcha", "beha'alotcha", "behalotja"]],
  "Sh'lach": ["Shlaj", ["shlaj", "shelaj", "shlach", "sh'lach", "shelaj lejá"]],
  "Korach": ["Koraj", ["koraj", "korach", "kóraj"]],
  "Chukat": ["Jukat", ["jukat", "chukat", "jukát"]],
  "Balak": ["Balak", ["balak"]],
  "Pinchas": ["Pinjás", ["pinjas", "pinchas", "pinejas"]],
  "Matot": ["Matot", ["matot", "mattot", "matos"]],
  "Masei": ["Masei", ["masei", "masey"]],
  "Devarim": ["Devarím", ["devarim", "devarím", "debarim"]],
  "Vaetchanan": ["Vaetjanán", ["vaetjanan", "vaetchanan", "vaetjanán"]],
  "Eikev": ["Ekev", ["ekev", "eikev", "ekeb"]],
  "Re'eh": ["Reé", ["ree", "reeh", "re'eh", "reé"]],
  "Shoftim": ["Shoftim", ["shoftim"]],
  "Ki Teitzei": ["Ki Tetzé", ["ki tetze", "ki tetzé", "ki teitzei", "ki tetzei", "ki-tetze"]],
  "Ki Tavo": ["Ki Tavó", ["ki tavo", "ki tavó", "ki-tavo"]],
  "Nitzavim": ["Nitzavim", ["nitzavim", "nitsavim", "nitzavím"]],
  "Vayeilech": ["Vaielej", ["vaielej", "vayelej", "vayeilech", "vayelech"]],
  "Ha'azinu": ["Haazinu", ["haazinu", "ha'azinu", "haazínu"]],
  "Vezot Haberakhah": ["Vezot Haberajá", ["vezot haberaja", "vezot haberakhah", "zot haberaja"]],
};
const faltan = parshiot.filter((p) => !ES[p]);
if (faltan.length) throw new Error("Faltan nombres en español: " + faltan.join(", "));

const LIBROS = { Genesis: "Génesis", Exodus: "Éxodo", Leviticus: "Levítico", Numbers: "Números", Deuteronomy: "Deuteronomio" };
const lectura = (partes) => {
  const l = getLeyningForParsha(partes);
  if (!l || !l.summary) throw new Error("Sin pasaje de la Torá para " + partes.join("-"));
  return l.summary.replace(/^(\w+)/, (m) => LIBROS[m] || m).replace(/(\d)-(\d)/g, "$1–$2");
};
const hebreo = (p) => Locale.gettext(p, "he-x-NoNikud");

// Fiestas que caen en Shabat (en la Diáspora): nombre en español
const FIESTA = [
  [/^Rosh Hashana/, "Rosh Hashaná"],
  [/^Yom Kippur$/, "Yom Kipur"],
  [/^Sukkot I$/, "Sucot"],
  [/^Sukkot .*\(CH''M\)$/, "Shabat Jol HaMoed Sucot"],
  [/^Shmini Atzeret$/, "Shemini Atzeret"],
  [/^Simchat Torah$/, "Simjat Torá"],
  [/^Pesach (I|VII|VIII)$/, "Pésaj"],
  [/^Pesach .*\(CH''M\)$/, "Shabat Jol HaMoed Pésaj"],
  [/^Shavuot/, "Shavuot"],
];
const nombres = []; // parashot (y combinadas)
const fiestas = [];
const idxNombre = new Map();
const idxFiesta = new Map();
const semanas = [];

for (let d = new Date(DESDE); d < HASTA; d = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 7)) {
  const hd = new HDate(d);
  const s = new Sedra(hd.getFullYear(), false).lookup(hd); // false = fuera de Israel (Diáspora)
  if (!s.chag) {
    const clave = s.parsha.join("-");
    if (!idxNombre.has(clave)) {
      idxNombre.set(clave, nombres.length);
      const es = s.parsha.map((p) => ES[p][0]).join("-");
      const al = [...new Set(s.parsha.flatMap((p) => ES[p][1]).concat(s.parsha.length > 1 ? [es.toLowerCase().replace(/-/g, " ")] : []))];
      nombres.push({ k: clave, es, he: s.parsha.map(hebreo).join("־"), lec: lectura(s.parsha), al });
    }
    semanas.push(idxNombre.get(clave));
  } else {
    const ev = (HebrewCalendar.getHolidaysOnDate(hd, false) || []).map((e) => e.getDesc());
    let es = null;
    for (const desc of ev) { const m = FIESTA.find(([re]) => re.test(desc)); if (m) { es = m[1]; break; } }
    if (!es) throw new Error("Fiesta sin nombre en español: " + JSON.stringify(ev) + " " + d.toDateString());
    if (!idxFiesta.has(es)) { idxFiesta.set(es, fiestas.length); fiestas.push({ es }); }
    semanas.push(-(idxFiesta.get(es) + 1));
  }
}
const salida = { desde: "2025-01-04", hasta: HASTA.getFullYear() - 1, nombres, fiestas, semanas };
writeFileSync(new URL("./parashot.json", import.meta.url), JSON.stringify(salida));
console.log(`Listo: ${semanas.length} Shabatot (2025-${HASTA.getFullYear() - 1}), ${nombres.length} parashot/combinadas, ${fiestas.length} fiestas:`, fiestas.map((f) => f.es).join(", "));
