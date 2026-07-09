# Migration Plan Documentation

## Overview
This migration adds two new fields to the `productos` table:
1. `bc3_descripcion_completa` - Concatenated BC3 description fields
2. `url_imagen` - Direct Azure image URLs imported from Excel

## Files
- `01_add_bc3_descripcion_completa.sql` - SQL script for Task 1
- `02_import_url_imagen.py` - Python script for Task 2
- `run_migration.sh` - Comprehensive migration script (run this!)
- `README.md` - This documentation

## Quick Start

### Option 1: Run Full Migration (Recommended)
```bash
cd /Volumes/WEBS/API_DISANO/migration
chmod +x run_migration.sh
./run_migration.sh
```

### Option 2: Run Tasks Separately
```bash
# Task 1: Add bc3_descripcion_completa
sqlite3 ../database/tarifa_disano.db < 01_add_bc3_descripcion_completa.sql

# Task 2: Import url_imagen
/Volumes/WEBS/disano-scraper/venv/bin/python3 02_import_url_imagen.py
```

### Option 3: Rollback
```bash
./run_migration.sh --rollback
```

## Task Details

### Task 1: Add bc3_descripcion_completa

**Purpose**: Concatenate `bc3_descripcion_corta` and `bc3_descripcion_larga` with separator

**Formula**: `bc3_descripcion_corta + '-----' + bc3_descripcion_larga`

**NULL Handling**: If `bc3_descripcion_corta` is NULL, result is NULL

**Expected Coverage**: 5,286 out of 8,288 rows (64%)

**Verification SQL**:
```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(bc3_descripcion_corta) as bc3_corta,
    COUNT(bc3_descripcion_larga) as bc3_larga,
    COUNT(bc3_descripcion_completa) as bc3_completa,
    ROUND(COUNT(bc3_descripcion_completa) * 100.0 / COUNT(*), 1) as percentage
FROM productos;
```

**Expected Result**:
- total_rows: 8288
- bc3_corta: 5286
- bc3_larga: 5286
- bc3_completa: 5286
- percentage: 63.8%

### Task 2: Import url_imagen

**Purpose**: Import direct Azure image URLs from Excel column 57

**Source**: `/Volumes/WEBS/disano-scraper/data/output/Tarifa_API_26_FINAL_COMPLETO.xlsx`

**Excel Column**: 57 (header: "Url_imagen")

**Match Key**: CÓDIGO column

**Data Type**: TEXT

**NULL Handling**: If Excel value is empty or NULL, database value is NULL

**Sample Data**:
```
https://azprodmedia.blob.core.windows.net/mediafiles/IP_safety23.jpg
https://azprodmedia.blob.core.windows.net/mediafiles/IP_safetyled.jpg
```

**Verification SQL**:
```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(url_imagen) as url_imagen,
    ROUND(COUNT(url_imagen) * 100.0 / COUNT(*), 1) as percentage
FROM productos;
```

**Expected Result**: Depends on Excel data (typically >90% coverage)

## Backup & Rollback

### Automatic Backup
The migration script creates an automatic backup before any changes:
- Location: `/Volumes/WEBS/API_DISANO/migration/backup/tarifa_disano_backup_YYYYMMDD_HHMMSS.db`
- Integrity check performed on backup

### Manual Rollback
```bash
# Option 1: Use the rollback script
./run_migration.sh --rollback

# Option 2: Manual restore
cp migration/backup/tarifa_disano_backup_YYYYMMDD_HHMMSS.db database/tarifa_disano.db
```

## Verification Steps

### After Full Migration
```sql
-- Check both new columns exist
PRAGMA table_info(productos);

-- Verify bc3_descripcion_completa
SELECT 
    CÓDIGO,
    bc3_descripcion_corta,
    bc3_descripcion_larga,
    substr(bc3_descripcion_completa, 1, 100) as bc3_completa_preview
FROM productos 
WHERE bc3_descripcion_completa IS NOT NULL 
LIMIT 5;

-- Verify url_imagen
SELECT 
    CÓDIGO,
    imagen,
    url_imagen,
    img_url
FROM productos 
WHERE url_imagen IS NOT NULL 
LIMIT 5;

-- Coverage summary
SELECT 
    COUNT(*) as total,
    COUNT(bc3_descripcion_completa) as bc3_completa,
    COUNT(url_imagen) as url_imagen
FROM productos;
```

## Idempotency

Both tasks are idempotent (safe to run multiple times):

- **Task 1**: SQL uses `ALTER TABLE ADD COLUMN IF NOT EXISTS` equivalent pattern
- **Task 2**: Python checks if column exists before adding; uses UPDATE which is idempotent

## Error Handling

### Task 1 Errors
- Column already exists: Script continues (idempotent)
- NULL values: Handled correctly with WHERE clause
- Index creation: Uses `IF NOT EXISTS`

### Task 2 Errors
- Excel file not found: Script exits with error
- Column mismatch: Script verifies Excel column header before import
- Missing codes: Logged but doesn't stop migration

## Performance

- **Task 1**: < 1 second (8,288 rows)
- **Task 2**: < 10 seconds (8,288 rows with Excel parsing)
- **Total migration time**: < 15 seconds

## Dependencies

- SQLite 3
- Python 3.14+
- openpyxl 3.1.0+
- Database and Excel files must be accessible

## Support

If you encounter issues:

1. Check backup exists: `ls -lh migration/backup/`
2. Verify database integrity: `sqlite3 database/tarifa_disano.db "PRAGMA integrity_check;"`
3. Check Excel file accessibility: `python3 -c "import openpyxl; openpyxl.load_workbook('...xlsx')"`
4. Review logs from individual task runs

## Next Steps

After migration:

1. Update API documentation to include new fields
2. Update database schema documentation
3. Consider adding indexes if these fields are queried frequently
4. Update any ETL pipelines that depend on these fields
