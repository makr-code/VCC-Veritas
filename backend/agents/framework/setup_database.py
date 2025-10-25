"""
VERITAS Agent Framework - Database Setup Script
================================================

Erstellt PostgreSQL-Tabellen für das Multi-Agent Research Plan System.

Usage:
    python backend/agents/framework/setup_database.py

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (optional)
    POSTGRES_HOST: PostgreSQL host (default: localhost)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_DB: Database name (default: veritas)
    POSTGRES_USER: Database user (default: postgres)
    POSTGRES_PASSWORD: Database password (default: postgres)

Created: 2025-10-08
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Setup PostgreSQL database for VERITAS Agent Framework."""
    
    def __init__(self):
        """Initialize database connection parameters."""
        # Try DATABASE_URL first
        self.database_url = os.getenv('DATABASE_URL')
        
        if not self.database_url:
            # Build from individual components
            self.host = os.getenv('POSTGRES_HOST', 'localhost')
            self.port = os.getenv('POSTGRES_PORT', '5432')
            self.database = os.getenv('POSTGRES_DB', 'veritas')
            self.user = os.getenv('POSTGRES_USER', 'postgres')
            # Prefer encrypted password from SecretsManager when available
            try:
                from backend.security.secrets import get_database_password
                secret_pw = get_database_password('POSTGRES')
            except Exception:
                secret_pw = None
            self.password = secret_pw or os.getenv('POSTGRES_PASSWORD', 'postgres')
            
            self.database_url = (
                f"postgresql://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}"
            )
        
        logger.info(f"Database setup initialized")
        logger.info(f"Target database: {self.database if hasattr(self, 'database') else 'from URL'}")
    
    def check_database_exists(self) -> bool:
        """Check if database exists."""
        try:
            # Connect to postgres database to check if target exists
            # Prefer pooled connection for control queries
            try:
                from backend.database.connection_pool import PostgresPool
                dsn = (
                    f"host={self.host} port={self.port} dbname=postgres user={self.user} password={self.password}"
                )
                # Create a temporary one-off pool for the 'postgres' DB if main pool points elsewhere
                pool = PostgresPool.instance()
                conn = psycopg2.connect(dsn)
            except Exception:
                conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database='postgres'
                )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.database,)
            )
            exists = cursor.fetchone() is not None
            
            cursor.close()
            conn.close()
            
            return exists
        except Exception as e:
            logger.error(f"Error checking database existence: {e}")
            return False
    
    def create_database(self) -> bool:
        """Create database if it doesn't exist."""
        try:
            if self.check_database_exists():
                logger.info(f"Database '{self.database}' already exists")
                return True
            
            logger.info(f"Creating database '{self.database}'...")
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(self.database)
                )
            )
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Database '{self.database}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating database: {e}")
            return False
    
    def execute_schema_file(self, schema_path: Path) -> bool:
        """Execute SQL schema file."""
        try:
            logger.info(f"Reading schema file: {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            logger.info(f"Connecting to database '{self.database}'...")
            
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            cursor = conn.cursor()
            
            logger.info("Executing schema SQL...")
            cursor.execute(schema_sql)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info("✅ Schema executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error executing schema: {e}")
            if 'conn' in locals():
                conn.rollback()
            return False
    
    def verify_tables(self) -> bool:
        """Verify that all required tables exist."""
        required_tables = [
            'research_plans',
            'research_plan_steps',
            'step_results',
            'agent_execution_log',
            'agent_registry_metadata'
        ]
        
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            cursor = conn.cursor()
            
            logger.info("Verifying tables...")
            
            for table in required_tables:
                cursor.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                    """,
                    (table,)
                )
                exists = cursor.fetchone()[0]
                
                if exists:
                    logger.info(f"  ✅ Table '{table}' exists")
                else:
                    logger.error(f"  ❌ Table '{table}' NOT found")
                    return False
            
            # Verify views
            cursor.execute(
                """
                SELECT viewname FROM pg_views 
                WHERE schemaname = 'public'
                """
            )
            views = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Views created: {', '.join(views)}")
            
            cursor.close()
            conn.close()
            
            logger.info("✅ All tables verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying tables: {e}")
            return False
    
    def get_table_stats(self) -> dict:
        """Get statistics about created tables."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            cursor = conn.cursor()
            
            stats = {}
            
            # Get table counts
            tables = [
                'research_plans',
                'research_plan_steps',
                'step_results',
                'agent_execution_log',
                'agent_registry_metadata'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            
            cursor.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}
    
    def setup(self) -> bool:
        """Run complete database setup."""
        logger.info("=" * 80)
        logger.info("VERITAS AGENT FRAMEWORK - DATABASE SETUP")
        logger.info("=" * 80)
        
        # Step 1: Create database if needed
        if not self.create_database():
            return False
        
        # Step 2: Execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            logger.error(f"❌ Schema file not found: {schema_path}")
            return False
        
        if not self.execute_schema_file(schema_path):
            return False
        
        # Step 3: Verify tables
        if not self.verify_tables():
            return False
        
        # Step 4: Show statistics
        logger.info("\n" + "=" * 80)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 80)
        
        stats = self.get_table_stats()
        for table, count in stats.items():
            logger.info(f"  {table}: {count} rows")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ DATABASE SETUP COMPLETE")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("  1. Run tests: pytest tests/agents/framework/")
        logger.info("  2. Start agent orchestrator")
        logger.info("  3. Create first research plan")
        
        return True


def main():
    """Main entry point."""
    try:
        setup = DatabaseSetup()
        success = setup.setup()
        
        if success:
            logger.info("\n✨ Setup completed successfully!")
            return 0
        else:
            logger.error("\n❌ Setup failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Setup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
