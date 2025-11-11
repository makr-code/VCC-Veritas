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

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SQLiteDatabaseSetup:
    """Setup SQLite database for VERITAS Agent Framework."""

    def __init__(self, db_path: str = None):
        """Initialize database path."""
        if db_path is None:
            # Default to data/agent_framework.db
            project_root = Path(__file__).parent.parent.parent.parent
            db_dir = project_root / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "agent_framework.db"
        else:
            self.db_path = Path(db_path)

        logger.info(f"Database path: {self.db_path}")

    def create_tables(self) -> bool:
        """Create all required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info("Creating tables...")

            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # ========================================
            # TABLE: research_plans
            # ========================================
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS research_plans (
                    -- Primary Key
                    plan_id TEXT PRIMARY KEY,

                    -- Plan Metadata
                    research_question TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    status TEXT NOT NULL DEFAULT 'pending',

                    -- Execution Tracking
                    current_step_index INTEGER DEFAULT 0,
                    total_steps INTEGER DEFAULT 0,
                    progress_percentage REAL DEFAULT 0.0,

                    -- Schema & Configuration
                    schema_name TEXT,
                    schema_version TEXT,
                    plan_document TEXT NOT NULL,  -- JSON

                    -- VERITAS-specific Fields
                    uds3_databases TEXT,  -- JSON array
                    phase5_hybrid_search INTEGER DEFAULT 1,  -- Boolean
                    security_level TEXT DEFAULT 'internal',
                    source_domains TEXT,  -- JSON array
                    query_complexity TEXT,

                    -- Results & Metadata
                    final_result TEXT,  -- JSON
                    execution_time_ms INTEGER,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,

                    -- Constraints
                    CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled'))
                )
            """
            )

            # Indexes for research_plans
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_plans_status ON research_plans(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_plans_created_at ON research_plans(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_plans_schema ON research_plans(schema_name)")

            # ========================================
            # TABLE: research_plan_steps
            # ========================================
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS research_plan_steps (
                    -- Primary Key
                    step_id TEXT PRIMARY KEY,

                    -- Foreign Key
                    plan_id TEXT NOT NULL REFERENCES research_plans(plan_id) ON DELETE CASCADE,

                    -- Step Metadata
                    step_index INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    step_type TEXT NOT NULL,

                    -- Agent Assignment
                    agent_name TEXT,
                    agent_type TEXT,
                    assigned_capability TEXT,

                    -- Execution Tracking
                    status TEXT NOT NULL DEFAULT 'pending',
                    started_at TEXT,
                    completed_at TEXT,
                    execution_time_ms INTEGER,

                    -- Step Configuration
                    step_config TEXT,  -- JSON
                    tool_name TEXT,
                    tool_input TEXT,  -- JSON

                    -- Dependencies
                    depends_on TEXT,  -- JSON array
                    parallel_group TEXT,

                    -- Results
                    result TEXT,  -- JSON
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,

                    -- Constraints
                    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
                    UNIQUE (plan_id, step_index)
                )
            """
            )

            # Indexes for research_plan_steps
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_steps_plan_id ON research_plan_steps(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_steps_status ON research_plan_steps(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_steps_agent_name ON research_plan_steps(agent_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_steps_step_index ON research_plan_steps(plan_id, step_index)")

            # ========================================
            # TABLE: step_results
            # ========================================
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS step_results (
                    -- Primary Key
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- Foreign Keys
                    step_id TEXT NOT NULL REFERENCES research_plan_steps(step_id) ON DELETE CASCADE,
                    plan_id TEXT NOT NULL REFERENCES research_plans(plan_id) ON DELETE CASCADE,

                    -- Result Metadata
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    result_type TEXT NOT NULL,

                    -- Result Data
                    result_data TEXT NOT NULL,  -- JSON
                    raw_output TEXT,

                    -- Quality Metrics
                    confidence_score REAL,
                    quality_score REAL,
                    source_count INTEGER,

                    -- VERITAS-specific Fields
                    uds3_search_results TEXT,  -- JSON
                    bm25_results TEXT,  -- JSON
                    hybrid_fusion_score REAL,
                    reranking_applied INTEGER DEFAULT 0,  -- Boolean

                    -- Metadata
                    metadata TEXT,  -- JSON

                    -- Constraints
                    CHECK (result_type IN (
                        'data_retrieval', 'data_analysis', 'synthesis',
                        'validation', 'final_answer', 'intermediate', 'error'
                    ))
                )
            """
            )

            # Indexes for step_results
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_step_id ON step_results(step_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_plan_id ON step_results(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_result_type ON step_results(result_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_created_at ON step_results(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_confidence ON step_results(confidence_score DESC)")

            # ========================================
            # TABLE: agent_execution_log
            # ========================================
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_execution_log (
                    -- Primary Key
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,

                    -- Foreign Keys
                    step_id TEXT REFERENCES research_plan_steps(step_id) ON DELETE CASCADE,
                    plan_id TEXT REFERENCES research_plans(plan_id) ON DELETE CASCADE,

                    -- Log Metadata
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    log_level TEXT NOT NULL,

                    -- Agent Information
                    agent_name TEXT,
                    agent_type TEXT,

                    -- Log Data
                    message TEXT NOT NULL,
                    context TEXT,  -- JSON

                    -- Performance Metrics
                    duration_ms INTEGER,
                    memory_mb INTEGER,

                    -- Error Tracking
                    error_type TEXT,
                    stack_trace TEXT,

                    -- Constraints
                    CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
                )
            """
            )

            # Indexes for agent_execution_log
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_step_id ON agent_execution_log(step_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_plan_id ON agent_execution_log(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_timestamp ON agent_execution_log(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_level ON agent_execution_log(log_level)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_agent ON agent_execution_log(agent_name)")

            # ========================================
            # TABLE: agent_registry_metadata
            # ========================================
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_registry_metadata (
                    -- Primary Key
                    agent_name TEXT PRIMARY KEY,

                    -- Agent Classification
                    agent_type TEXT NOT NULL,
                    domain TEXT,

                    -- Capabilities
                    capabilities TEXT NOT NULL,  -- JSON array
                    tools TEXT,  -- JSON array

                    -- Configuration
                    default_config TEXT,  -- JSON
                    schema_name TEXT,

                    -- Status
                    is_active INTEGER DEFAULT 1,  -- Boolean
                    is_migrated INTEGER DEFAULT 0,  -- Boolean
                    migration_date TEXT,

                    -- Metadata
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    version TEXT,

                    -- Performance Stats
                    total_executions INTEGER DEFAULT 0,
                    success_rate REAL,
                    avg_execution_time_ms INTEGER
                )
            """
            )

            # Indexes for agent_registry_metadata
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_registry_type ON agent_registry_metadata(agent_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_registry_domain ON agent_registry_metadata(domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_registry_active ON agent_registry_metadata(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_registry_migrated ON agent_registry_metadata(is_migrated)")

            conn.commit()
            logger.info("✅ Tables created successfully")

            # Insert sample data
            self._insert_sample_data(cursor)
            conn.commit()

            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False

    def _insert_sample_data(self, cursor):
        """Insert sample agent metadata."""
        logger.info("Inserting sample data...")

        sample_agents = [
            {
                "agent_name": "environmental",
                "agent_type": "DataRetrievalAgent",
                "domain": "environmental",
                "capabilities": json.dumps(["query_processing", "data_analysis", "environmental_data"]),
                "tools": json.dumps(["uds3", "database", "api_call"]),
                "default_config": json.dumps({"max_results": 10, "use_hybrid_search": True}),
                "is_active": 1,
                "is_migrated": 0,
            },
            {
                "agent_name": "pipeline_manager",
                "agent_type": "OrchestratorAgent",
                "domain": "orchestration",
                "capabilities": json.dumps(["query_processing", "pipeline_management"]),
                "tools": json.dumps(["database"]),
                "default_config": json.dumps({"queue_size": 100, "worker_count": 4}),
                "is_active": 1,
                "is_migrated": 1,
            },
            {
                "agent_name": "registry",
                "agent_type": "AgentRegistry",
                "domain": "registry",
                "capabilities": json.dumps(["agent_registration", "capability_matching"]),
                "tools": json.dumps(["uds3", "database", "vector_search", "api_call"]),
                "default_config": json.dumps({"cache_ttl": 300}),
                "is_active": 1,
                "is_migrated": 1,
            },
        ]

        for agent in sample_agents:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO agent_registry_metadata
                    (agent_name, agent_type, domain, capabilities, tools, default_config, is_active, is_migrated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        agent["agent_name"],
                        agent["agent_type"],
                        agent["domain"],
                        agent["capabilities"],
                        agent["tools"],
                        agent["default_config"],
                        agent["is_active"],
                        agent["is_migrated"],
                    ),
                )
            except Exception as e:
                logger.warning(f"Could not insert {agent['agent_name']}: {e}")

        logger.info("✅ Sample data inserted")

    def verify_tables(self) -> bool:
        """Verify that all required tables exist."""
        required_tables = [
            "research_plans",
            "research_plan_steps",
            "step_results",
            "agent_execution_log",
            "agent_registry_metadata",
        ]

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            logger.info("Verifying tables...")

            for table in required_tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                exists = cursor.fetchone() is not None

                if exists:
                    logger.info(f"  ✅ Table '{table}' exists")
                else:
                    logger.error(f"  ❌ Table '{table}' NOT found")
                    return False

            conn.close()
            logger.info("✅ All tables verified successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error verifying tables: {e}")
            return False

    def get_table_stats(self) -> dict:
        """Get statistics about created tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {}

            tables = [
                "research_plans",
                "research_plan_steps",
                "step_results",
                "agent_execution_log",
                "agent_registry_metadata",
            ]

            for table in tables:
                # table values sourced from internal schema introspection, not user input.  # nosec B608  # internal introspection
                cursor.execute(f"SELECT COUNT(*) FROM {table}")  # nosec B608  # internal table name from validated list
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
