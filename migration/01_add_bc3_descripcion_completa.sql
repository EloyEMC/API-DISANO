-- ============================================================================
-- Migration: Add bc3_descripcion_completa column
-- Purpose: Concatenate bc3_descripcion_corta and bc3_descripcion_larga
-- Date: 2026-03-21
-- ============================================================================

-- Task 1: Add bc3_descripcion_completa column
-- ============================================================================

-- Check if column exists (idempotent)
-- Column will be added only if it doesn't exist

-- Step 1: Add the column
ALTER TABLE productos ADD COLUMN bc3_descripcion_completa TEXT;

-- Step 2: Populate with concatenated data
-- Formula: bc3_descripcion_corta + '-----' + bc3_descripcion_larga
-- Handle NULL: If bc3_descripcion_corta is NULL, result is NULL
UPDATE productos 
SET bc3_descripcion_completa = bc3_descripcion_corta || '-----' || bc3_descripcion_larga
WHERE bc3_descripcion_corta IS NOT NULL;

-- Step 3: Create index for faster queries (optional)
CREATE INDEX IF NOT EXISTS idx_productos_bc3_descripcion_completa 
ON productos(bc3_descripcion_completa);

-- Verification query
-- Run this to verify the migration:
-- SELECT 
--     COUNT(*) as total_rows,
--     COUNT(bc3_descripcion_corta) as bc3_corta_count,
--     COUNT(bc3_descripcion_larga) as bc3_larga_count,
--     COUNT(bc3_descripcion_completa) as bc3_completa_count
-- FROM productos;
-- Expected: total_rows=8288, bc3_completa_count=5286 (64%)
