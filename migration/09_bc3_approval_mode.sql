-- Explicit approval mode for durable BC3 and catalog-import snapshots.
ALTER TABLE bc3_enrichment_previews
    ADD COLUMN IF NOT EXISTS approval_mode TEXT DEFAULT 'github_review';
ALTER TABLE bc3_enrichment_previews
    ALTER COLUMN approval_mode SET DEFAULT 'github_review';
UPDATE bc3_enrichment_previews
   SET approval_mode = 'github_review'
 WHERE approval_mode IS NULL;

ALTER TABLE catalog_import_snapshots
    ADD COLUMN IF NOT EXISTS approval_mode TEXT DEFAULT 'github_review';
ALTER TABLE catalog_import_snapshots
    ALTER COLUMN approval_mode SET DEFAULT 'github_review';
UPDATE catalog_import_snapshots
   SET approval_mode = 'github_review'
 WHERE approval_mode IS NULL;
ALTER TABLE catalog_import_snapshots
ADD COLUMN IF NOT EXISTS github_approval_verified_at TIMESTAMP;
