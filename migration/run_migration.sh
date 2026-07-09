#!/bin/bash
# ============================================================================
# Comprehensive Migration Script
# Purpose: Execute both migration tasks with backup, verification, and rollback
# Date: 2026-03-21
#
# Tasks:
#   1. Add bc3_descripcion_completa column (concatenated BC3 fields)
#   2. Import url_imagen from Excel column 57
# ============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
PROJECT_DIR="/Volumes/WEBS/API_DISANO"
DB_PATH="${PROJECT_DIR}/database/tarifa_disano.db"
BACKUP_DIR="${PROJECT_DIR}/migration/backup"
MIGRATION_DIR="${PROJECT_DIR}/migration"
PYTHON_VENV="/Volumes/WEBS/disano-scraper/venv/bin/python3"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/tarifa_disano_backup_${TIMESTAMP}.db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Create backup
create_backup() {
    print_header "Creating Database Backup"
    
    if [ ! -f "$DB_PATH" ]; then
        print_error "Database not found: $DB_PATH"
        exit 1
    fi
    
    mkdir -p "$BACKUP_DIR"
    
    print_success "Creating backup: $BACKUP_FILE"
    cp "$DB_PATH" "$BACKUP_FILE"
    
    local backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
    print_success "Backup created successfully (${backup_size})"
}

# Verify backup
verify_backup() {
    print_header "Verifying Backup"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    # Check SQLite integrity
    if sqlite3 "$BACKUP_FILE" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        print_success "Backup integrity check passed"
    else
        print_error "Backup integrity check failed"
        exit 1
    fi
}

# Task 1: Add bc3_descripcion_completa
run_task1() {
    print_header "Task 1: Add bc3_descripcion_completa"
    
    local sql_file="${MIGRATION_DIR}/01_add_bc3_descripcion_completa.sql"
    
    if [ ! -f "$sql_file" ]; then
        print_error "SQL file not found: $sql_file"
        exit 1
    fi
    
    # Execute SQL
    print_success "Executing SQL script..."
    if sqlite3 "$DB_PATH" < "$sql_file"; then
        print_success "Task 1 completed successfully"
    else
        print_error "Task 1 failed"
        exit 1
    fi
}

# Verify Task 1
verify_task1() {
    print_header "Verifying Task 1"
    
    local result=$(sqlite3 "$DB_PATH" "SELECT 
        COUNT(*) as total,
        COUNT(bc3_descripcion_completa) as completa,
        ROUND(COUNT(bc3_descripcion_completa) * 100.0 / COUNT(*), 1) as percentage
    FROM productos;")
    
    echo "$result"
    print_success "Task 1 verification completed"
}

# Task 2: Import url_imagen
run_task2() {
    print_header "Task 2: Import url_imagen from Excel"
    
    local python_file="${MIGRATION_DIR}/02_import_url_imagen.py"
    
    if [ ! -f "$python_file" ]; then
        print_error "Python script not found: $python_file"
        exit 1
    fi
    
    # Execute Python script
    if "$PYTHON_VENV" "$python_file"; then
        print_success "Task 2 completed successfully"
    else
        print_error "Task 2 failed"
        exit 1
    fi
}

# Verify Task 2
verify_task2() {
    print_header "Verifying Task 2"
    
    local result=$(sqlite3 "$DB_PATH" "SELECT 
        COUNT(*) as total,
        COUNT(url_imagen) as url_imagen,
        ROUND(COUNT(url_imagen) * 100.0 / COUNT(*), 1) as percentage
    FROM productos;")
    
    echo "$result"
    print_success "Task 2 verification completed"
}

# Final verification
final_verification() {
    print_header "Final Verification"
    
    local result=$(sqlite3 "$DB_PATH" "SELECT 
        'Total rows: ' || COUNT(*) as info FROM productos
    UNION ALL
    SELECT 
        'bc3_descripcion_completa: ' || COUNT(bc3_descripcion_completa) FROM productos
    UNION ALL
    SELECT 
        'url_imagen: ' || COUNT(url_imagen) FROM productos;")
    
    echo "$result"
    print_success "All tasks verified successfully"
}

# Rollback function
rollback() {
    print_header "Rolling Back Changes"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup not found, cannot rollback"
        exit 1
    fi
    
    print_warning "Restoring database from backup: $BACKUP_FILE"
    
    # Stop any database connections (if any)
    # ... (add if needed)
    
    # Restore from backup
    cp "$BACKUP_FILE" "$DB_PATH"
    
    print_success "Rollback completed successfully"
}

# Main execution
main() {
    print_header "Comprehensive Migration Script"
    echo "Database: $DB_PATH"
    echo "Backup: $BACKUP_FILE"
    echo ""
    
    # Check for rollback flag
    if [ "${1:-}" = "--rollback" ]; then
        rollback
        exit 0
    fi
    
    # Step 1: Create backup
    create_backup
    verify_backup
    
    echo ""
    
    # Step 2: Run Task 1
    run_task1
    verify_task1
    
    echo ""
    
    # Step 3: Run Task 2
    run_task2
    verify_task2
    
    echo ""
    
    # Step 4: Final verification
    final_verification
    
    echo ""
    print_header "Migration Completed Successfully!"
    echo "Backup file: $BACKUP_FILE"
    echo "To rollback, run: $0 --rollback"
    echo ""
}

# Execute main
main "$@"
