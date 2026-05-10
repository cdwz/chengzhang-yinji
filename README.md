# 成长印记 (ChengZhang YinJi)

> 家校协同分层自主学习与过程评价系统

## 项目简介

"成长印记"是一个合规、安全、易用的Web应用，实现学生分层自主学习任务管理、学科过程性评价记录、多维度数据分析。严格遵循教育部"双减"政策及四川省"人工智能+教育"行动计划。

## 核心功能

- **分层自主学习任务**：教师按学习小组发布任务，家长拍照记录
- **学科过程性评价**：多维度自定义评价，表格化录入
- **正向激励与成长档案**：个人成长进度，匿名班级概况
- **数据分析与报告**：周/月/学期/学年报告生成

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL 15
- Redis 7
- MinIO (对象存储)

### 前端
- Vue 3 + TypeScript
- Vite
- Vant UI (移动端)
- Element Plus (PC端)

## 合规说明

系统严格遵循教育政策法规：
- 禁止词汇：排名、排行榜、快慢班、好差生、打卡、每日必做
- 替代词汇：个人成长进度、班级分布概况、学习小组、选做建议
- 所有任务强制标记为【选做】
- 家长端仅展示匿名统计，不显示其他学生信息

## 项目结构

```
czyj/
├── backend/           # FastAPI 后端
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
├── frontend/          # Vue3 前端
│   ├── src/
│   ├── public/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 本地开发

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置
alembic upgrade head
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 部署

详见 `docker-compose.yml` 和部署文档。

## 许可证

MIT License
