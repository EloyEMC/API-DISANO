# Complete Migration Plan - Summary

## Migration Overview

This migration plan implements **TWO** new fields in the `productos` table:

### 1. bc3_descripcion_completa (SQL-based)
- **Type**: TEXT
- **Formula**: `bc3_descripcion_corta || '-----' || bc3_descripcion_larga`
- **Coverage**: 5,286 out of 8,288 rows (63.8%)
- **Implementation**: SQL ALTER + UPDATE

### 2. url_imagen (Excel import)
- **Type**: TEXT
- **Source**: Excel column 57 ("Url_imagen")
- **Match key**: CÓDIGO column
- **Coverage**: Expected >90%
- **Implementation**: Python script with openpyxl

---

## Files Created

```
/Volumes/WEBS/API_DISANO/migration/
├── 01_add_bc3_descripcion_completa.sql    # Task 1: SQL script
├── 02_import_url_imagen.py                 # Task 2: Python import script
├── run_migration.sh                         # Combined execution script
├── README.md                                # Full documentation
├── backup/                                  # Backup directory
└── SUMMARY.md                               # This file
```

---

## Quick Start (Recommended)

```bash
cd /Volumes/WEBS/API_DISANO/migration
./run_migration.sh
```

This will:
1. ✅ Create automatic backup
2. ✅ Add bc3_descripcion_completa column
3. ✅ Import url_imagen from Excel
4. ✅ Verify both tasks
5. ✅ Provide rollback instructions

---

## Execution Options

### Option 1: Full Migration (Recommended)
```bash
./run_migration.sh
```

### Option 2: Individual Tasks
```bash
# Task 1 only
sqlite3 ../database/tarifa_disano.db < 01_add_bc3_descripcion_completa.sql

# Task 2 only
/Volumes/WEBS/disano-scraper/venv/bin/python3 02_import_url_imagen.py
```

### Option 3: Rollback
```bash
./run_migration.sh --rollback
```

---

## Task 1 Details: bc3_descripcion_completa

### SQL Implementation

**Add column**:
```sql
ALTER TABLE productos ADD COLUMN bc3_descripcion_completa TEXT;
```

**Populate data**:
```sql
UPDATE productos 
SET bc3_descripcion_completa = bc3_descripcion_corta || '-----' || bc3_descripcion_larga
WHERE bc3_descripcion_corta IS NOT NULL;
```

**Create index** (optional):
```sql
CREATE INDEX IF NOT EXISTS idx_productos_bc3_descripcion_completa 
ON productos(bc3_descripcion_completa);
```

### Expected Results

| Metric | Value |
|--------|-------|
| Total rows | 8,288 |
| Rows with data | 5,286 (63.8%) |
| Execution time | < 1 second |

### Verification SQL
```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(bc3_descripcion_corta) as bc3_corta,
    COUNT(bc3_descripcion_larga) as bc3_larga,
    COUNT(bc3_descripcion_completa) as bc3_completa,
    ROUND(COUNT(bc3_descripcion_completa) * 100.0 / COUNT(*), 1) as percentage
FROM productos;
```

**Expected output**:
```
total_rows: 8288
bc3_corta: 5286
bc3_larga: 5286
bc3_completa: 5286
percentage: 63.8
```

---

## Task 2 Details: url_imagen

### Python Implementation

**Script**: `02_import_url_imagen.py`

**Features**:
- ✅ Idempotent (safe to run multiple times)
- ✅ Verifies Excel column header before import
- ✅ Handles NULL/empty values correctly
- ✅ Batch updates for performance
- ✅ Detailed progress reporting
- ✅ Verification statistics

**Configuration**:
```python
DB_PATH = '/Volumes/WEBS/API_DISANO/database/tarifa_disano.db'
EXCEL_PATH = '/Volumes/WEBS/disano-scraper/data/output/Tarifa_API_26_FINAL_COMPLETO.xlsx'
EXCEL_COLUMN_INDEX = 57  # Column number (1-based)
EXCEL_COLUMN_HEADER = 'Url_imagen'
```

### Sample Data

| CÓDIGO | url_imagen |
|--------|-----------|
| 11253300 | https://azprodmedia.blob.core.windows.net/mediafiles/IP_safety23.jpg |
| 11253400 | https://azprodmedia.blob.core.windows.net/mediafiles/IP_safety23.jpg |
| 11253500 | https://azprodmedia.blob.core.windows.net/mediafiles/IP_safetyled.jpg |

### Verification SQL
```sql
SELECT 
    COUNT(*) as total_rows,
    COUNT(url_imagen) as url_imagen,
    ROUND(COUNT(url_imagen) * 100.0 / COUNT(*), 1) as percentage
FROM productos;
```

---

## Backup & Rollback

### Automatic Backup

**Location**: `/Volumes/WEBS/API_DISANO/migration/backup/tarifa_disano_backup_YYYYMMDD_HHMMSS.db`

**Features**:
- ✅ Created before any changes
- ✅ Integrity check performed
- ✅ Used for rollback

### Rollback Procedure

**Option 1: Using script** (Recommended)
```bash
./run_migration.sh --rollback
```

**Option 2: Manual restore**
```bash
cp migration/backup/tarifa_disano_backup_YYYYMMDD_HHMMSS.db database/tarifa_disano.db
```

---

## Verification Steps

### After Full Migration

```sql
-- 1. Check columns exist
PRAGMA table_info(productos);

-- 2. Verify bc3_descripcion_completa
SELECT 
    CÓDIGO,
    substr(bc3_descripcion_corta, 1, 50) as corta_preview,
    substr(bc3_descripcion_completa, 1, 100) as completa_preview
FROM productos 
WHERE bc3_descripcion_completa IS NOT NULL 
LIMIT 3;

-- 3. Verify url_imagen
SELECT 
    CÓDIGO,
    imagen,
    substr(url_imagen, 1, 70) as url_imagen_preview,
    substr(img_url, 1, 70) as img_url_preview
FROM productos 
WHERE url_imagen IS NOT NULL 
LIMIT 3;

-- 4. Coverage summary
SELECT 
    'Total rows' as metric,
    COUNT(*) as value
FROM productos
UNION ALL
SELECT 
    'bc3_descripcion_completa',
    COUNT(bc3_descripcion_completa)
FROM productos
UNION ALL
SELECT 
    'url_imagen',
    COUNT(url_imagen)
FROM productos;
```

---

## Idempotency & Safety

### Idempotent Design

Both tasks are **safe to run multiple times**:

- **Task 1**: SQL UPDATE is idempotent by nature
- **Task 2**: Python script checks if column exists before adding

### Safety Features

- ✅ Automatic backup before changes
- ✅ Integrity check on backup
- ✅ Verification after each task
- ✅ Detailed logging
- ✅ Rollback capability
- ✅ Error handling

---

## Performance Estimates

| Task | Estimated Time |
|------|---------------|
| Backup creation | < 2 seconds |
| Task 1 (bc3_descripcion_completa) | < 1 second |
| Task 2 (url_imagen import) | < 10 seconds |
| Verification | < 1 second |
| **Total** | **< 15 seconds** |

---

## Dependencies

- **SQLite 3** (for database operations)
- **Python 3.14+** (for Excel import)
- **openpyxl 3.1.0+** (for Excel parsing)
- **Database file**: `/Volumes/WEBS/API_DISANO/database/tarifa_disano.db`
- **Excel file**: `/Volumes/WEBS/disano-scraper/data/output/Tarifa_API_26_FINAL_COMPLETO.xlsx`

---

## Next Steps After Migration

1. ✅ Update API documentation to include new fields
2. ✅ Update database schema documentation
3. ✅ Consider adding indexes if these fields are queried frequently
4. ✅ Update ETL pipelines that depend on these fields
5. ✅ Test API endpoints with new fields

---

## Troubleshooting

### Common Issues

**Issue**: Excel file not found
```bash
# Check file exists
ls -lh /Volumes/WEBS/disano-scraper/data/output/Tarifa_API_26_FINAL_COMPLETO.xlsx
```

**Issue**: Column already exists
```bash
# This is normal, script is idempotent
# Continue with migration
```

**Issue**: Backup integrity check failed
```bash
# Manually create backup
cp database/tarifa_disano.db migration/backup/manual_backup.db
# Then run migration again
```

---

## Support & Documentation

For detailed documentation, see: `/Volumes/WEBS/API_DISANO/migration/README.md`

---

**Migration Status**: Ready to execute 🚀
**Estimated Duration**: < 15 seconds
**Risk Level**: Low (with automatic backup and rollback)
