"""
迁移脚本：添加 Class.subjects、LearningTask.target_type、LearningTask.target_ids 字段
执行：python -m scripts.migrate_add_subjects_targets
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def migrate():
    async with engine.begin() as conn:
        # 1. Class 表添加 subjects 字段
        try:
            await conn.execute(text(
                "ALTER TABLE classes ADD COLUMN subjects JSONB DEFAULT '[\"语文\", \"数学\", \"英语\"]'"
            ))
            print("✅ classes.subjects 字段已添加")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print("⏭️ classes.subjects 字段已存在，跳过")
            else:
                raise

        # 2. LearningTask 表添加 target_type 字段
        try:
            await conn.execute(text(
                "ALTER TABLE learning_tasks ADD COLUMN target_type VARCHAR(20) DEFAULT 'all'"
            ))
            print("✅ learning_tasks.target_type 字段已添加")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print("⏭️ learning_tasks.target_type 字段已存在，跳过")
            else:
                raise

        # 3. LearningTask 表添加 target_ids 字段
        try:
            await conn.execute(text(
                "ALTER TABLE learning_tasks ADD COLUMN target_ids JSONB DEFAULT '[]'"
            ))
            print("✅ learning_tasks.target_ids 字段已添加")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print("⏭️ learning_tasks.target_ids 字段已存在，跳过")
            else:
                raise

        # 4. 更新已有数据：将 group_id 不为空的记录的 target_type 设为 'groups'
        result = await conn.execute(text(
            "UPDATE learning_tasks SET target_type = 'groups', target_ids = CAST(CONCAT('[\"', group_id, '\"]') AS JSONB) WHERE group_id IS NOT NULL AND target_type = 'all'"
        ))
        print(f"✅ 已更新 {result.rowcount} 条任务记录的 target_type")

    print("\n🎉 迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
