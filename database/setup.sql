-- ================================================================
-- SETUP DE BASE DE DATOS SUPABASE
-- ================================================================
-- Ejecuta este script en: Supabase Dashboard → SQL Editor → New Query
-- ================================================================

-- 1. CREAR LA TABLA DE MÉTRICAS
CREATE TABLE IF NOT EXISTS metrics (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ts          TIMESTAMPTZ DEFAULT now(),
    total_count INTEGER DEFAULT 0,
    data        JSONB DEFAULT '{}'::jsonb
);

-- 2. HABILITAR ROW LEVEL SECURITY (RLS)
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;

-- 3. POLÍTICA: Permitir que CUALQUIERA pueda LEER (SELECT) con la anon key
CREATE POLICY "Lectura pública de métricas"
    ON metrics
    FOR SELECT
    TO anon
    USING (true);

-- 4. POLÍTICA: Permitir que CUALQUIERA pueda INSERTAR con la anon key
CREATE POLICY "Inserción pública de métricas"
    ON metrics
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- 5. HABILITAR REALTIME en la tabla
-- (Esto permite que el frontend reciba datos en tiempo real via WebSocket)
ALTER PUBLICATION supabase_realtime ADD TABLE metrics;

-- 6. CREAR ÍNDICE para consultas rápidas por timestamp
CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics (ts DESC);

-- ================================================================
-- ¡LISTO! Después de ejecutar esto, la tabla estará lista para 
-- recibir datos del backend Python y enviarlos al frontend web.
-- ================================================================
