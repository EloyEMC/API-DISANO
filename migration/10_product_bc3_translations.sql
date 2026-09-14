-- Add the BC3 Catalan and Galician descriptions emitted by catalog imports.
-- Additive and repeat-safe; existing rows remain NULL unless explicitly populated.
ALTER TABLE productos
    ADD COLUMN IF NOT EXISTS bc3_descripcion_corta_ca TEXT;
ALTER TABLE productos
    ADD COLUMN IF NOT EXISTS bc3_descripcion_larga_ca TEXT;
ALTER TABLE productos
    ADD COLUMN IF NOT EXISTS bc3_descripcion_corta_gl TEXT;
ALTER TABLE productos
    ADD COLUMN IF NOT EXISTS bc3_descripcion_larga_gl TEXT;
