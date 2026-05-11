-- 为班级表添加 subjects 字段
ALTER TABLE classes ADD COLUMN IF NOT EXISTS subjects JSONB DEFAULT '["语文", "数学", "英语"]';

-- 为学习任务表添加 target_type 字段
ALTER TABLE learning_tasks ADD COLUMN IF NOT EXISTS target_type VARCHAR(20) DEFAULT 'all';

-- 为学习任务表添加 target_ids 字段  
ALTER TABLE learning_tasks ADD COLUMN IF NOT EXISTS target_ids JSONB DEFAULT '[]';

-- 更新已有数据：将group_id不为空的记录的target_type设为'groups'
UPDATE learning_tasks 
SET target_type = 'groups', 
    target_ids = CAST(CONCAT('["', group_id, '"]') AS JSONB) 
WHERE group_id IS NOT NULL AND target_type = 'all';

-- 显示迁移结果
SELECT 'classes.subjects 字段已添加' as result;
SELECT COUNT(*) as existing_classes FROM classes;
SELECT COUNT(*) as existing_tasks FROM learning_tasks;