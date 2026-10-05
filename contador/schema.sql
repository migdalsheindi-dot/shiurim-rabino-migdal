-- Total de reproducciones por shiur
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
