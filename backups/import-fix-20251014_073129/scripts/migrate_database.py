"""
VERITAS Framework - Database Migration System

This module provides a lightweight database migration system for managing
schema changes across environments.

Features:
- Version-based migrations
- Automatic migration tracking
- Rollback support
- Safe migration execution
- PostgreSQL, MySQL, SQLite support

Usage:
    # Create new migration
    python scripts/migrate_database.py create "add_user_table"
    
    # Run pending migrations
    python scripts/migrate_database.py migrate
    
    # Rollback last migration
    python scripts/migrate_database.py rollback
    
    # Show migration status
    python scripts/migrate_database.py status

Author: VERITAS Team
Date: 2025-10-08
Version: 1.0.0
"""

import os
import sys
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2 import sql
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False

try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


@dataclass
class Migration:
    """Migration metadata."""
    version: int
    name: str
    filename: str
    checksum: str
    applied_at: Optional[datetime] = None


class DatabaseMigrator:
    """Database migration manager."""
    
    def __init__(self, migrations_dir: Path, db_type: str = "sqlite", **db_config):
        """
        Initialize migrator.
        
        Args:
            migrations_dir: Directory containing migration files
            db_type: Database type (sqlite, postgresql, mysql)
            **db_config: Database connection parameters
        """
        self.migrations_dir = migrations_dir
        self.db_type = db_type
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """Connect to database."""
        if self.db_type == "sqlite":
            db_path = self.db_config.get("path", "./data/veritas.sqlite")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
            
        elif self.db_type == "postgresql":
            if not HAS_POSTGRESQL:
                raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
            
            self.conn = psycopg2.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 5432),
                database=self.db_config.get("database", "veritas"),
                user=self.db_config.get("user", "veritas_user"),
                password=self.db_config.get("password", "")
            )
            self.cursor = self.conn.cursor()
            
        elif self.db_type == "mysql":
            if not HAS_MYSQL:
                raise ImportError("PyMySQL not installed. Install with: pip install pymysql")
            
            self.conn = pymysql.connect(
                host=self.db_config.get("host", "localhost"),
                port=self.db_config.get("port", 3306),
                database=self.db_config.get("database", "veritas"),
                user=self.db_config.get("user", "veritas_user"),
                password=self.db_config.get("password", "")
            )
            self.cursor = self.conn.cursor()
            
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def disconnect(self):
        """Disconnect from database."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def init_migrations_table(self):
        """Create migrations tracking table."""
        if self.db_type == "sqlite":
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        elif self.db_type == "postgresql":
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        elif self.db_type == "mysql":
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    checksum VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        self.conn.commit()
    
    def get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations."""
        self.cursor.execute(
            "SELECT version, name, checksum, applied_at FROM schema_migrations ORDER BY version"
        )
        
        migrations = []
        for row in self.cursor.fetchall():
            migrations.append(Migration(
                version=row[0],
                name=row[1],
                checksum=row[2],
                applied_at=row[3]
            ))
        
        return migrations
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        applied = {m.version for m in self.get_applied_migrations()}
        available = self.get_available_migrations()
        
        pending = [m for m in available if m.version not in applied]
        return sorted(pending, key=lambda m: m.version)
    
    def get_available_migrations(self) -> List[Migration]:
        """Get list of available migrations from files."""
        migrations = []
        
        for filepath in sorted(self.migrations_dir.glob("*.sql")):
            # Parse filename: 001_create_users_table.sql
            parts = filepath.stem.split("_", 1)
            if len(parts) != 2:
                continue
            
            try:
                version = int(parts[0])
            except ValueError:
                continue
            
            name = parts[1]
            
            # Calculate checksum
            with open(filepath, "rb") as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
            
            migrations.append(Migration(
                version=version,
                name=name,
                filename=str(filepath),
                checksum=checksum
            ))
        
        return sorted(migrations, key=lambda m: m.version)
    
    def create_migration(self, name: str) -> Path:
        """
        Create new migration file.
        
        Args:
            name: Migration name
            
        Returns:
            Path to created migration file
        """
        # Get next version number
        available = self.get_available_migrations()
        next_version = max([m.version for m in available], default=0) + 1
        
        # Create filename
        filename = f"{next_version:03d}_{name}.sql"
        filepath = self.migrations_dir / filename
        
        # Create template
        template = f"""-- Migration: {name}
-- Version: {next_version}
-- Created: {datetime.now().isoformat()}
-- 
-- Description: 
-- TODO: Add migration description
--

-- ============================================================================
-- UP Migration
-- ============================================================================

-- Add your migration SQL here
-- Example:
-- CREATE TABLE users (
--     id SERIAL PRIMARY KEY,
--     username VARCHAR(255) NOT NULL UNIQUE,
--     email VARCHAR(255) NOT NULL UNIQUE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );


-- ============================================================================
-- DOWN Migration (for rollback)
-- ============================================================================
-- Separate rollback SQL with: -- ROLLBACK --

-- ROLLBACK --

-- Add your rollback SQL here
-- Example:
-- DROP TABLE IF EXISTS users;
"""
        
        with open(filepath, "w") as f:
            f.write(template)
        
        print(f"✅ Created migration: {filename}")
        print(f"   Edit the file and add your SQL statements")
        
        return filepath
    
    def migrate(self, dry_run: bool = False) -> int:
        """
        Run pending migrations.
        
        Args:
            dry_run: If True, don't actually run migrations
            
        Returns:
            Number of migrations applied
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✅ No pending migrations")
            return 0
        
        print(f"Found {len(pending)} pending migration(s)")
        print()
        
        count = 0
        for migration in pending:
            print(f"Applying migration {migration.version}: {migration.name}...")
            
            if dry_run:
                print("  [DRY RUN] Would execute migration")
                continue
            
            # Read migration file
            with open(migration.filename, "r") as f:
                sql = f.read()
            
            # Split on rollback marker
            parts = sql.split("-- ROLLBACK --")
            up_sql = parts[0].strip()
            
            try:
                # Execute migration
                self.cursor.executescript(up_sql) if self.db_type == "sqlite" else \
                    self.cursor.execute(up_sql)
                
                # Record migration
                self.cursor.execute(
                    "INSERT INTO schema_migrations (version, name, checksum) VALUES (?, ?, ?)"
                    if self.db_type == "sqlite" else
                    "INSERT INTO schema_migrations (version, name, checksum) VALUES (%s, %s, %s)",
                    (migration.version, migration.name, migration.checksum)
                )
                
                self.conn.commit()
                count += 1
                print(f"  ✅ Applied migration {migration.version}")
                
            except Exception as e:
                self.conn.rollback()
                print(f"  ❌ Error applying migration {migration.version}: {str(e)}")
                raise
        
        print()
        print(f"✅ Applied {count} migration(s)")
        return count
    
    def rollback(self, steps: int = 1) -> int:
        """
        Rollback last N migrations.
        
        Args:
            steps: Number of migrations to rollback
            
        Returns:
            Number of migrations rolled back
        """
        applied = self.get_applied_migrations()
        
        if not applied:
            print("✅ No migrations to rollback")
            return 0
        
        to_rollback = applied[-steps:]
        print(f"Rolling back {len(to_rollback)} migration(s)")
        print()
        
        count = 0
        for migration in reversed(to_rollback):
            print(f"Rolling back migration {migration.version}: {migration.name}...")
            
            # Find migration file
            filepath = self.migrations_dir / f"{migration.version:03d}_{migration.name}.sql"
            
            if not filepath.exists():
                print(f"  ⚠️  Migration file not found: {filepath}")
                continue
            
            # Read migration file
            with open(filepath, "r") as f:
                sql = f.read()
            
            # Extract rollback SQL
            parts = sql.split("-- ROLLBACK --")
            if len(parts) < 2:
                print(f"  ⚠️  No rollback SQL found in migration")
                continue
            
            down_sql = parts[1].strip()
            
            try:
                # Execute rollback
                self.cursor.executescript(down_sql) if self.db_type == "sqlite" else \
                    self.cursor.execute(down_sql)
                
                # Remove migration record
                self.cursor.execute(
                    "DELETE FROM schema_migrations WHERE version = ?" if self.db_type == "sqlite"
                    else "DELETE FROM schema_migrations WHERE version = %s",
                    (migration.version,)
                )
                
                self.conn.commit()
                count += 1
                print(f"  ✅ Rolled back migration {migration.version}")
                
            except Exception as e:
                self.conn.rollback()
                print(f"  ❌ Error rolling back migration {migration.version}: {str(e)}")
                raise
        
        print()
        print(f"✅ Rolled back {count} migration(s)")
        return count
    
    def status(self):
        """Show migration status."""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        print("=" * 80)
        print("Migration Status")
        print("=" * 80)
        print()
        
        print(f"Database: {self.db_type}")
        print(f"Migrations directory: {self.migrations_dir}")
        print()
        
        print(f"Total migrations: {len(available)}")
        print(f"Applied: {len(applied)}")
        print(f"Pending: {len(pending)}")
        print()
        
        if applied:
            print("Applied Migrations:")
            print("-" * 80)
            for m in applied:
                print(f"  ✅ {m.version:03d} - {m.name} (applied {m.applied_at})")
            print()
        
        if pending:
            print("Pending Migrations:")
            print("-" * 80)
            for m in pending:
                print(f"  ⏳ {m.version:03d} - {m.name}")
            print()
        
        print("=" * 80)


def main():
    """Main CLI function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VERITAS Database Migration Tool")
    parser.add_argument("command", choices=["create", "migrate", "rollback", "status"],
                       help="Migration command")
    parser.add_argument("name", nargs="?", help="Migration name (for create command)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't execute)")
    parser.add_argument("--steps", type=int, default=1, help="Number of steps to rollback")
    parser.add_argument("--db-type", default=os.getenv("DB_TYPE", "sqlite"),
                       help="Database type (sqlite, postgresql, mysql)")
    
    args = parser.parse_args()
    
    # Database configuration from environment
    db_config = {}
    if args.db_type == "sqlite":
        db_config["path"] = os.getenv("SQLITE_DB_PATH", "./data/veritas.sqlite")
    elif args.db_type == "postgresql":
        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "veritas"),
            "user": os.getenv("DB_USER", "veritas_user"),
            "password": os.getenv("DB_PASSWORD", "")
        }
    elif args.db_type == "mysql":
        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_NAME", "veritas"),
            "user": os.getenv("DB_USER", "veritas_user"),
            "password": os.getenv("DB_PASSWORD", "")
        }
    
    # Migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    # Create migrator
    with DatabaseMigrator(migrations_dir, args.db_type, **db_config) as migrator:
        # Initialize migrations table
        migrator.init_migrations_table()
        
        # Execute command
        if args.command == "create":
            if not args.name:
                print("❌ Migration name required for 'create' command")
                sys.exit(1)
            migrator.create_migration(args.name)
            
        elif args.command == "migrate":
            migrator.migrate(dry_run=args.dry_run)
            
        elif args.command == "rollback":
            migrator.rollback(steps=args.steps)
            
        elif args.command == "status":
            migrator.status()


if __name__ == "__main__":
    main()
