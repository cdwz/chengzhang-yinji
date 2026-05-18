-- 添加周末/节假日字段到 learning_tasks 表
ALTER TABLE learning_tasks 
ADD COLUMN IF NOT EXISTS weekend_required BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS holiday_required BOOLEAN DEFAULT FALSE;

-- 更新已有记录的默认值
UPDATE learning_tasks 
SET weekend_required = TRUE, holiday_required = FALSE 
WHERE weekend_required IS NULL OR holiday_required IS NULL;
