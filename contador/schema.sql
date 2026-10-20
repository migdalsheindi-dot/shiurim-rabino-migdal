-- Total de reproducciones por shiur (desde siempre)
CREATE TABLE IF NOT EXISTS reproducciones (
  shiur_id TEXT PRIMARY KEY,
  total INTEGER NOT NULL DEFAULT 0
);

-- Huellas anónimas de las últimas 6 horas (para no contar dos veces a la misma
-- persona). Se borran solas con cada reproducción nueva.
CREATE TABLE IF NOT EXISTS oyentes (
  huella TEXT PRIMARY KEY,
  ts INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_oyentes_ts ON oyentes (ts);

-- ---- Estadísticas del Panel Admin (todo agregado por día, sin datos personales) ----

-- Visitas por día: totales, visitantes únicos y reparto celular / computadora
CREATE TABLE IF NOT EXISTS dias (
  dia TEXT PRIMARY KEY,            -- AAAA-MM-DD (hora de Argentina)
  visitas INTEGER NOT NULL DEFAULT 0,
  unicos INTEGER NOT NULL DEFAULT 0,
  mobile INTEGER NOT NULL DEFAULT 0,
  desktop INTEGER NOT NULL DEFAULT 0
);

-- Huellas de visitantes del día (para contar únicos). Se borran a los 2 días.
CREATE TABLE IF NOT EXISTS visitantes (
  dia TEXT NOT NULL,
  huella TEXT NOT NULL,
  PRIMARY KEY (dia, huella)
);

-- Páginas más vistas: "inicio", "busqueda", "tema:Tania", "shiur:<id>"
CREATE TABLE IF NOT EXISTS paginas (
  dia TEXT NOT NULL,
  pagina TEXT NOT NULL,
  total INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (dia, pagina)
);

-- Escucha por shiur y por día: reproducciones contadas y segundos escuchados
CREATE TABLE IF NOT EXISTS escucha_dia (
  dia TEXT NOT NULL,
  shiur_id TEXT NOT NULL,
  reproducciones INTEGER NOT NULL DEFAULT 0,
  segundos INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (dia, shiur_id)
);

-- Eventos de donación: donar_abrir (abrió el aviso) y donar_click (fue a Mercado Pago),
-- con desde dónde (encabezado, menu, modal) y en qué parte de la web estaba
CREATE TABLE IF NOT EXISTS eventos (
  dia TEXT NOT NULL,
  tipo TEXT NOT NULL,
  origen TEXT NOT NULL,
  contexto TEXT NOT NULL,
  total INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (dia, tipo, origen, contexto)
);
