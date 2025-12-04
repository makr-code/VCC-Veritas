"""
VERITAS Agent Framework - SQLite Database Setup
================================================

SQLite implementation of the Agent Framework database.
Compatible with PostgreSQL schema for easy migration.

Usage:
    python backend/agents/framework/setup_database_sqlite.py

Database Location:
    data/agent_framework.db

Created: 2025-10-08
"""

import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

            # Use a static mapping of allowed internal queries to avoid any
            # runtime string interpolation that static analyzers flag as
            # dynamic SQL (Bandit B608). These queries are fixed and internal.
            queries = {
                "research_plans": "SELECT COUNT(*) FROM research_plans",
                "research_plan_steps": "SELECT COUNT(*) FROM research_plan_steps",
                "step_results": "SELECT COUNT(*) FROM step_results",
                "agent_execution_log": "SELECT COUNT(*) FROM agent_execution_log",
                "agent_registry_metadata": "SELECT COUNT(*) FROM agent_registry_metadata",
            }

            for table in tables:
                query = queries.get(table)
                if not query:
                    logger.error(f"No query defined for internal table: {table}")
                    continue

                cursor.execute(query)
                count = cursor.fetchone()[0]
                stats[table] = count

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"Error getting table stats: {e}")
            return {}

    def setup(self) -> bool:
        """Run complete database setup."""
        logger.info("=" * 80)
        logger.info("VERITAS AGENT FRAMEWORK - SQLite DATABASE SETUP")
        logger.info("=" * 80)
        logger.info(f"Database: {self.db_path}")
        logger.info("")

        # Create tables
        if not self.create_tables():
            return False

        # Verify tables
        if not self.verify_tables():
            return False

        # Show statistics
        logger.info("\n" + "=" * 80)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 80)

        stats = self.get_table_stats()
        for table, count in stats.items():
            logger.info(f"  {table}: {count} rows")

        logger.info("\n" + "=" * 80)
        logger.info("✅ DATABASE SETUP COMPLETE")
        logger.info("=" * 80)
        logger.info("\nDatabase location:")
        logger.info(f"  {self.db_path}")
        logger.info("\nNext steps:")
        logger.info("  1. Run tests: pytest tests/agents/framework/")
        logger.info("  2. Create BaseAgent implementation")
        logger.info("  3. Create first research plan")

        return True


def main():
    """Main entry point."""
    try:
        setup = SQLiteDatabaseSetup()
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
