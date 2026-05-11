#!/usr/bin/env python3
"""
简单迁移脚本 - 直接使用 psycopg2
"""
import os
import sys
import psycopg2
from psycopg2.extras import Json
from urllib.parse import urlparse

# 从环境变量获取数据库连接
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://czyj:Czyj@2026Dev@20.20.30.81:5433/czyj_db')

# 解析数据库URL
if DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')

parsed = urlparse(DATABASE_URL)
db_config = {
    'host': parsed.hostname,
    'port': parsed.port,
    'database': parsed.path[1:],  # 去掉开头的 '/'
    'user': parsed.username,
    'password': parsed.password
}

print(f"连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")

try:
    # 连接数据库
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("✅ 数据库连接成功")
    
    # 1. 添加 subjects 字段
    try:
        cursor.execute("ALTER TABLE classes ADD COLUMN subjects JSONB DEFAULT '[\"语文\", \"数学\", \"英语\"]'")
        print("✅ classes.subjects 字段已添加")
    except psycopg2.Error as e:
        if 'already exists' in str(e) or 'duplicate' in str(e).lower():
            print("⏭️ classes.subjects 字段已存在，跳过")
        else:
            raise
    
    # 2. 添加 target_type 字段
    try:
        cursor.execute("ALTER TABLE learning_tasks ADD COLUMN target_type VARCHAR(20) DEFAULT 'all'")
        print("✅ learning_tasks.target_type 字段已添加")
    except psycopg2.Error as e:
        if 'already exists' in str(e) or 'duplicate' in str(e).lower():
            print("⏭️ learning_tasks.target_type 字段已存在，跳过")
        else:
            raise
    
    # 3. 添加 target_ids 字段
    try:
        cursor.execute("ALTER TABLE learning_tasks ADD COLUMN target_ids JSONB DEFAULT '[]'")
        print("✅ learning_tasks.target_ids 字段已添加")
    except psycopg2.Error as e:
        if 'already exists' in str(e) or 'duplicate' in str(e).lower():
            print("⏭️ learning_tasks.target_ids 字段已存在，跳过")
        else:
            raise
    
    # 4. 更新已有数据
    cursor.execute("""
        UPDATE learning_tasks 
        SET target_type = 'groups', 
            target_ids = CAST(CONCAT('["', group_id, '"]') AS JSONB) 
        WHERE group_id IS NOT NULL AND target_type = 'all'
    """)
    print(f"✅ 已更新 {cursor.rowcount} 条任务记录的 target_type")
    
    # 5. 显示统计
    cursor.execute("SELECT COUNT(*) FROM classes")
    class_count = cursor.fetchone()[0]
    print(f"📊 现有班级数: {class_count}")
    
    cursor.execute("SELECT COUNT(*) FROM learning_tasks")
    task_count = cursor.fetchone()[0]
    print(f"📊 现有任务数: {task_count}")
    
    cursor.close()
    conn.close()
    
    print("\n🎉 迁移完成！")
    
except Exception as e:
    print(f"❌ 迁移失败: {e}")
    sys.exit(1)