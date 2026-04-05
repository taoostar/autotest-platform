-- Performance Report Database Migration
-- Date: 2026-04-05

-- 1. performance_logs 表扩展
ALTER TABLE performance_logs ADD COLUMN IF NOT EXISTS load_avg_1 FLOAT;
ALTER TABLE performance_logs ADD COLUMN IF NOT EXISTS load_avg_5 FLOAT;
ALTER TABLE performance_logs ADD COLUMN IF NOT EXISTS load_avg_15 FLOAT;
ALTER TABLE performance_logs ADD COLUMN IF NOT EXISTS process_data JSONB;
ALTER TABLE performance_logs ADD COLUMN IF NOT EXISTS result_id INTEGER REFERENCES task_results(id);
ALTER TABLE performance_logs ADD COLUMN IF NOT EXISTS fd_count INTEGER DEFAULT 0;

-- 2. task_results 表扩展
ALTER TABLE task_results ADD COLUMN IF NOT EXISTS perf_summary JSONB;

-- 3. test_plans 表扩展
ALTER TABLE test_plans ADD COLUMN IF NOT EXISTS collect_performance BOOLEAN DEFAULT TRUE;
ALTER TABLE test_plans ADD COLUMN IF NOT EXISTS process_keyword VARCHAR(100);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_performance_logs_result_id ON performance_logs(result_id);
CREATE INDEX IF NOT EXISTS idx_performance_logs_task_id ON performance_logs(task_id);

-- 回滚脚本
-- ALTER TABLE performance_logs DROP COLUMN IF EXISTS load_avg_1;
-- ALTER TABLE performance_logs DROP COLUMN IF EXISTS load_avg_5;
-- ALTER TABLE performance_logs DROP COLUMN IF EXISTS load_avg_15;
-- ALTER TABLE performance_logs DROP COLUMN IF EXISTS process_data;
-- ALTER TABLE performance_logs DROP COLUMN IF EXISTS result_id;
-- ALTER TABLE performance_logs DROP COLUMN IF EXISTS fd_count;
-- ALTER TABLE task_results DROP COLUMN IF EXISTS perf_summary;
-- ALTER TABLE test_plans DROP COLUMN IF EXISTS collect_performance;
-- ALTER TABLE test_plans DROP COLUMN IF EXISTS process_keyword;
-- DROP INDEX IF EXISTS idx_performance_logs_result_id;
-- DROP INDEX IF EXISTS idx_performance_logs_task_id;
