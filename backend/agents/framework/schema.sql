-- VERITAS AGENT FRAMEWORK - DATABASE SCHEMA
-- =========================================
--
-- PostgreSQL Schema for Multi-Agent Research Plan Execution
--
-- Based on: codespaces-blank mockup framework
-- Adapted for: VERITAS Agent System
-- Created: 2025-10-08
--
-- TABLES:
-- - research_plans: Main research plan storage
-- - research_plan_steps: Individual execution steps
-- - step_results: Results from each step execution
-- - agent_registry: Agent metadata and capabilities

-- ========================================
-- TABLE: research_plans
-- ========================================
-- Stores complete research plans with metadata

CREATE TABLE IF NOT EXISTS research_plans (
    -- Primary Key
    plan_id VARCHAR(255) PRIMARY KEY,

    -- Plan Metadata
    research_question TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',

    -- Execution Tracking
    current_step_index INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    progress_percentage DECIMAL(5,2) DEFAULT 0.0,

    -- Schema & Configuration
    schema_name VARCHAR(255),
    schema_version VARCHAR(50),
    plan_document JSONB NOT NULL,

    -- VERITAS-specific Fields
    uds3_databases TEXT[],
    phase5_hybrid_search BOOLEAN DEFAULT true,
    security_level VARCHAR(50) DEFAULT 'internal',
    source_domains TEXT[],
    query_complexity VARCHAR(50),

    -- Results & Metadata
    final_result JSONB,
    execution_time_ms INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Indexing
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled'))
);

-- Indexes for research_plans
CREATE INDEX IF NOT EXISTS idx_research_plans_status ON research_plans(status);
CREATE INDEX IF NOT EXISTS idx_research_plans_created_at ON research_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_research_plans_schema ON research_plans(schema_name);
CREATE INDEX IF NOT EXISTS idx_research_plans_domains ON research_plans USING GIN(source_domains);
CREATE INDEX IF NOT EXISTS idx_research_plans_plan_document ON research_plans USING GIN(plan_document);


-- ========================================
-- TABLE: research_plan_steps
-- ========================================
-- Individual execution steps within a research plan

CREATE TABLE IF NOT EXISTS research_plan_steps (
    -- Primary Key
    step_id VARCHAR(255) PRIMARY KEY,

    -- Foreign Key
    plan_id VARCHAR(255) NOT NULL REFERENCES research_plans(plan_id) ON DELETE CASCADE,

    -- Step Metadata
    step_index INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL,

    -- Agent Assignment
    agent_name VARCHAR(255),
    agent_type VARCHAR(100),
    assigned_capability VARCHAR(255),

    -- Execution Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,

    -- Step Configuration
    step_config JSONB,
    tool_name VARCHAR(255),
    tool_input JSONB,

    -- Dependencies
    depends_on TEXT[],
    parallel_group VARCHAR(100),

    -- Results
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Constraints
    CONSTRAINT valid_step_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    CONSTRAINT unique_step_per_plan UNIQUE (plan_id, step_index)
);

-- Indexes for research_plan_steps
CREATE INDEX IF NOT EXISTS idx_steps_plan_id ON research_plan_steps(plan_id);
CREATE INDEX IF NOT EXISTS idx_steps_status ON research_plan_steps(status);
CREATE INDEX IF NOT EXISTS idx_steps_agent_name ON research_plan_steps(agent_name);
CREATE INDEX IF NOT EXISTS idx_steps_step_index ON research_plan_steps(plan_id, step_index);
CREATE INDEX IF NOT EXISTS idx_steps_dependencies ON research_plan_steps USING GIN(depends_on);


-- ========================================
-- TABLE: step_results
-- ========================================
-- Detailed results and artifacts from step execution

CREATE TABLE IF NOT EXISTS step_results (
    -- Primary Key
    result_id SERIAL PRIMARY KEY,

    -- Foreign Keys
    step_id VARCHAR(255) NOT NULL REFERENCES research_plan_steps(step_id) ON DELETE CASCADE,
    plan_id VARCHAR(255) NOT NULL REFERENCES research_plans(plan_id) ON DELETE CASCADE,

    -- Result Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    result_type VARCHAR(100) NOT NULL,

    -- Result Data
    result_data JSONB NOT NULL,
    raw_output TEXT,

    -- Quality Metrics
    confidence_score DECIMAL(5,4),
    quality_score DECIMAL(5,4),
    source_count INTEGER,

    -- VERITAS-specific Fields
    uds3_search_results JSONB,
    bm25_results JSONB,
    hybrid_fusion_score DECIMAL(5,4),
    reranking_applied BOOLEAN DEFAULT false,

    -- Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT valid_result_type CHECK (result_type IN (
        'data_retrieval', 'data_analysis', 'synthesis',
        'validation', 'final_answer', 'intermediate', 'error'
    ))
);

-- Indexes for step_results
CREATE INDEX IF NOT EXISTS idx_results_step_id ON step_results(step_id);
CREATE INDEX IF NOT EXISTS idx_results_plan_id ON step_results(plan_id);
CREATE INDEX IF NOT EXISTS idx_results_result_type ON step_results(result_type);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON step_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_confidence ON step_results(confidence_score DESC);


-- ========================================
-- TABLE: agent_execution_log
-- ========================================
-- Detailed logging of agent execution for debugging and monitoring

CREATE TABLE IF NOT EXISTS agent_execution_log (
    -- Primary Key
    log_id SERIAL PRIMARY KEY,

    -- Foreign Keys
    step_id VARCHAR(255) REFERENCES research_plan_steps(step_id) ON DELETE CASCADE,
    plan_id VARCHAR(255) REFERENCES research_plans(plan_id) ON DELETE CASCADE,

    -- Log Metadata
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    log_level VARCHAR(20) NOT NULL,

    -- Agent Information
    agent_name VARCHAR(255),
    agent_type VARCHAR(100),

    -- Log Data
    message TEXT NOT NULL,
    context JSONB,

    -- Performance Metrics
    duration_ms INTEGER,
    memory_mb INTEGER,

    -- Error Tracking
    error_type VARCHAR(255),
    stack_trace TEXT,

    -- Constraints
    CONSTRAINT valid_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Indexes for agent_execution_log
CREATE INDEX IF NOT EXISTS idx_log_step_id ON agent_execution_log(step_id);
CREATE INDEX IF NOT EXISTS idx_log_plan_id ON agent_execution_log(plan_id);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON agent_execution_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_level ON agent_execution_log(log_level);
CREATE INDEX IF NOT EXISTS idx_log_agent ON agent_execution_log(agent_name);


-- ========================================
-- TABLE: agent_registry_metadata
-- ========================================
-- Extended agent metadata for framework integration

CREATE TABLE IF NOT EXISTS agent_registry_metadata (
    -- Primary Key
    agent_name VARCHAR(255) PRIMARY KEY,

    -- Agent Classification
    agent_type VARCHAR(100) NOT NULL,
    domain VARCHAR(100),

    -- Capabilities
    capabilities TEXT[] NOT NULL,
    tools TEXT[],

    -- Configuration
    default_config JSONB,
    schema_name VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_migrated BOOLEAN DEFAULT false,
    migration_date TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(50),

    -- Performance Stats
    total_executions INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    avg_execution_time_ms INTEGER
);

-- Indexes for agent_registry_metadata
CREATE INDEX IF NOT EXISTS idx_registry_type ON agent_registry_metadata(agent_type);
CREATE INDEX IF NOT EXISTS idx_registry_domain ON agent_registry_metadata(domain);
CREATE INDEX IF NOT EXISTS idx_registry_active ON agent_registry_metadata(is_active);
CREATE INDEX IF NOT EXISTS idx_registry_migrated ON agent_registry_metadata(is_migrated);
CREATE INDEX IF NOT EXISTS idx_registry_capabilities ON agent_registry_metadata USING GIN(capabilities);


-- ========================================
-- VIEWS
-- ========================================

-- Active Research Plans Overview
CREATE OR REPLACE VIEW active_research_plans AS
SELECT
    plan_id,
    research_question,
    status,
    current_step_index,
    total_steps,
    progress_percentage,
    created_at,
    updated_at,
    schema_name,
    source_domains,
    security_level
FROM research_plans
WHERE status IN ('pending', 'running', 'paused')
ORDER BY created_at DESC;


-- Step Execution Summary
CREATE OR REPLACE VIEW step_execution_summary AS
SELECT
    s.plan_id,
    s.step_id,
    s.step_name,
    s.agent_name,
    s.status,
    s.execution_time_ms,
    COUNT(r.result_id) as result_count,
    AVG(r.confidence_score) as avg_confidence,
    AVG(r.quality_score) as avg_quality
FROM research_plan_steps s
LEFT JOIN step_results r ON s.step_id = r.step_id
GROUP BY s.plan_id, s.step_id, s.step_name, s.agent_name, s.status, s.execution_time_ms;


-- Agent Performance Stats
CREATE OR REPLACE VIEW agent_performance_stats AS
SELECT
    agent_name,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
    ROUND(
        100.0 * COUNT(CASE WHEN status = 'completed' THEN 1 END) / NULLIF(COUNT(*), 0),
        2
    ) as success_rate,
    AVG(execution_time_ms) as avg_execution_time_ms,
    MIN(execution_time_ms) as min_execution_time_ms,
    MAX(execution_time_ms) as max_execution_time_ms
FROM research_plan_steps
WHERE agent_name IS NOT NULL
GROUP BY agent_name
ORDER BY total_executions DESC;


-- ========================================
-- TRIGGERS
-- ========================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_research_plans_updated_at
    BEFORE UPDATE ON research_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_registry_updated_at
    BEFORE UPDATE ON agent_registry_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- Auto-update progress percentage
CREATE OR REPLACE FUNCTION update_plan_progress()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE research_plans
    SET
        progress_percentage = (
            SELECT ROUND(
                100.0 * COUNT(CASE WHEN status = 'completed' THEN 1 END) / NULLIF(COUNT(*), 0),
                2
            )
            FROM research_plan_steps
            WHERE plan_id = NEW.plan_id
        ),
        current_step_index = (
            SELECT COALESCE(MAX(step_index), 0)
            FROM research_plan_steps
            WHERE plan_id = NEW.plan_id
            AND status = 'completed'
        )
    WHERE plan_id = NEW.plan_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_progress_on_step_completion
    AFTER UPDATE OF status ON research_plan_steps
    FOR EACH ROW
    WHEN (NEW.status = 'completed' OR NEW.status = 'failed')
    EXECUTE FUNCTION update_plan_progress();


-- ========================================
-- SAMPLE DATA (for testing)
-- ========================================

-- Insert sample agent metadata
INSERT INTO agent_registry_metadata (
    agent_name, agent_type, domain, capabilities, tools,
    default_config, is_active, is_migrated
) VALUES
(
    'environmental',
    'DataRetrievalAgent',
    'environmental',
    ARRAY['query_processing', 'data_analysis', 'environmental_data'],
    ARRAY['uds3', 'database', 'api_call'],
    '{"max_results": 10, "use_hybrid_search": true}'::jsonb,
    true,
    false
),
(
    'pipeline_manager',
    'OrchestratorAgent',
    'orchestration',
    ARRAY['query_processing', 'pipeline_management'],
    ARRAY['database'],
    '{"queue_size": 100, "worker_count": 4}'::jsonb,
    true,
    true
),
(
    'registry',
    'AgentRegistry',
    'registry',
    ARRAY['agent_registration', 'capability_matching'],
    ARRAY['uds3', 'database', 'vector_search', 'api_call'],
    '{"cache_ttl": 300}'::jsonb,
    true,
    true
)
ON CONFLICT (agent_name) DO NOTHING;


-- ========================================
-- COMMENTS
-- ========================================

COMMENT ON TABLE research_plans IS 'Stores complete research plans with execution tracking';
COMMENT ON TABLE research_plan_steps IS 'Individual execution steps within a research plan';
COMMENT ON TABLE step_results IS 'Detailed results and artifacts from step execution';
COMMENT ON TABLE agent_execution_log IS 'Detailed logging of agent execution for debugging';
COMMENT ON TABLE agent_registry_metadata IS 'Extended agent metadata for framework integration';

COMMENT ON COLUMN research_plans.plan_id IS 'Unique identifier for the research plan';
COMMENT ON COLUMN research_plans.plan_document IS 'Complete JSON schema-validated research plan';
COMMENT ON COLUMN research_plans.uds3_databases IS 'Array of UDS3 databases to search';
COMMENT ON COLUMN research_plans.phase5_hybrid_search IS 'Enable Phase 5 hybrid search (BM25+UDS3)';

COMMENT ON COLUMN research_plan_steps.step_id IS 'Unique identifier for the step';
COMMENT ON COLUMN research_plan_steps.depends_on IS 'Array of step_ids this step depends on';
COMMENT ON COLUMN research_plan_steps.parallel_group IS 'Group identifier for parallel execution';

COMMENT ON COLUMN step_results.hybrid_fusion_score IS 'Reciprocal Rank Fusion score for hybrid results';
COMMENT ON COLUMN step_results.reranking_applied IS 'Whether reranking was applied to results';
