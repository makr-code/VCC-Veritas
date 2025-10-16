#!/bin/bash
#
# VERITAS Framework - Database Backup Script
#
# This script performs automated backups of the PostgreSQL database
# and optionally uploads to remote storage (S3, Azure Blob, etc.)
#
# Usage:
#   ./backup_database.sh
#
# Environment Variables:
#   DB_HOST             - Database host (default: localhost)
#   DB_PORT             - Database port (default: 5432)
#   DB_NAME             - Database name (default: veritas)
#   DB_USER             - Database user (default: veritas_user)
#   DB_PASSWORD         - Database password (required)
#   BACKUP_PATH         - Backup directory (default: ./backups)
#   BACKUP_RETENTION_DAYS - Days to keep backups (default: 30)
#   REMOTE_BACKUP_ENABLED - Enable remote backup (default: false)
#   REMOTE_BACKUP_TYPE  - Remote storage type (s3, azure, gcs)
#   REMOTE_BACKUP_BUCKET - Remote storage bucket/container
#
# Author: VERITAS Team
# Date: 2025-10-08
# Version: 1.0.0
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# =============================================================================
# Configuration
# =============================================================================

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-veritas}"
DB_USER="${DB_USER:-veritas_user}"
DB_PASSWORD="${DB_PASSWORD:?Database password required}"

BACKUP_PATH="${BACKUP_PATH:-./backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_COMPRESSION="${BACKUP_COMPRESSION:-true}"

REMOTE_BACKUP_ENABLED="${REMOTE_BACKUP_ENABLED:-false}"
REMOTE_BACKUP_TYPE="${REMOTE_BACKUP_TYPE:-s3}"
REMOTE_BACKUP_BUCKET="${REMOTE_BACKUP_BUCKET:-}"

# =============================================================================
# Functions
# =============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
    exit 1
}

# Create backup directory
create_backup_dir() {
    if [ ! -d "$BACKUP_PATH" ]; then
        log "Creating backup directory: $BACKUP_PATH"
        mkdir -p "$BACKUP_PATH" || error "Failed to create backup directory"
    fi
}

# Perform database backup
backup_database() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_PATH}/veritas_${timestamp}.sql"
    
    log "Starting database backup..."
    log "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
    log "Backup file: $backup_file"
    
    # Set password for pg_dump
    export PGPASSWORD="$DB_PASSWORD"
    
    # Perform backup
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --clean --if-exists --create --verbose > "$backup_file" 2>/dev/null; then
        log "✅ Database backup completed: $backup_file"
    else
        error "Failed to backup database"
    fi
    
    # Compress backup
    if [ "$BACKUP_COMPRESSION" = "true" ]; then
        log "Compressing backup..."
        gzip "$backup_file" || error "Failed to compress backup"
        backup_file="${backup_file}.gz"
        log "✅ Backup compressed: $backup_file"
    fi
    
    # Calculate size
    local size=$(du -h "$backup_file" | cut -f1)
    log "Backup size: $size"
    
    echo "$backup_file"
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up backups older than ${BACKUP_RETENTION_DAYS} days..."
    
    local count=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((count++))
    done < <(find "$BACKUP_PATH" -name "veritas_*.sql*" -mtime +${BACKUP_RETENTION_DAYS} -print0)
    
    if [ $count -gt 0 ]; then
        log "✅ Removed $count old backup(s)"
    else
        log "No old backups to remove"
    fi
}

# Upload to S3
upload_to_s3() {
    local backup_file="$1"
    
    log "Uploading backup to S3..."
    
    if ! command -v aws &> /dev/null; then
        log "⚠️  AWS CLI not installed, skipping S3 upload"
        return
    fi
    
    local s3_path="s3://${REMOTE_BACKUP_BUCKET}/veritas/$(basename $backup_file)"
    
    if aws s3 cp "$backup_file" "$s3_path"; then
        log "✅ Backup uploaded to S3: $s3_path"
    else
        log "⚠️  Failed to upload to S3"
    fi
}

# Upload to Azure Blob Storage
upload_to_azure() {
    local backup_file="$1"
    
    log "Uploading backup to Azure Blob Storage..."
    
    if ! command -v az &> /dev/null; then
        log "⚠️  Azure CLI not installed, skipping Azure upload"
        return
    fi
    
    local blob_name="veritas/$(basename $backup_file)"
    
    if az storage blob upload \
        --container-name "$REMOTE_BACKUP_BUCKET" \
        --name "$blob_name" \
        --file "$backup_file" \
        --overwrite; then
        log "✅ Backup uploaded to Azure: $blob_name"
    else
        log "⚠️  Failed to upload to Azure"
    fi
}

# Upload to Google Cloud Storage
upload_to_gcs() {
    local backup_file="$1"
    
    log "Uploading backup to Google Cloud Storage..."
    
    if ! command -v gsutil &> /dev/null; then
        log "⚠️  gsutil not installed, skipping GCS upload"
        return
    fi
    
    local gcs_path="gs://${REMOTE_BACKUP_BUCKET}/veritas/$(basename $backup_file)"
    
    if gsutil cp "$backup_file" "$gcs_path"; then
        log "✅ Backup uploaded to GCS: $gcs_path"
    else
        log "⚠️  Failed to upload to GCS"
    fi
}

# Upload backup to remote storage
upload_backup() {
    local backup_file="$1"
    
    if [ "$REMOTE_BACKUP_ENABLED" != "true" ]; then
        return
    fi
    
    if [ -z "$REMOTE_BACKUP_BUCKET" ]; then
        log "⚠️  REMOTE_BACKUP_BUCKET not set, skipping remote upload"
        return
    fi
    
    case "$REMOTE_BACKUP_TYPE" in
        s3)
            upload_to_s3 "$backup_file"
            ;;
        azure)
            upload_to_azure "$backup_file"
            ;;
        gcs)
            upload_to_gcs "$backup_file"
            ;;
        *)
            log "⚠️  Unknown remote backup type: $REMOTE_BACKUP_TYPE"
            ;;
    esac
}

# =============================================================================
# Main
# =============================================================================

main() {
    log "=" * 80
    log "VERITAS Database Backup"
    log "=" * 80
    
    # Create backup directory
    create_backup_dir
    
    # Perform backup
    backup_file=$(backup_database)
    
    # Upload to remote storage
    upload_backup "$backup_file"
    
    # Cleanup old backups
    cleanup_old_backups
    
    log "=" * 80
    log "✅ Backup completed successfully!"
    log "=" * 80
}

# Run main function
main "$@"
