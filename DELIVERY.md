# 成长印记 - 项目交付报告

## 项目概述

**项目名称**：成长印记（ChengZhang YinJi）  
**定位**：家校协同分层自主学习任务管理与过程评价系统  
**政策合规**：严格遵循教育部"双减"政策与四川省"AI+教育"行动计划

---

## 技术架构

### 后端技术栈
- **框架**：FastAPI 0.115.0
- **ORM**：SQLAlchemy 2.0.31
- **数据库**：PostgreSQL 15 + asyncpg
- **缓存**：Redis 7
- **对象存储**：MinIO
- **认证**：JWT + bcrypt密码哈希
- **迁移**：Alembic 1.13.2

### 前端技术栈
- **框架**：Vue 3.4 + TypeScript 5.4
- **构建工具**：Vite 5.2
- **UI组件**：
  - 教师端：Element Plus
  - 家长端：Vant UI
- **状态管理**：Pinia
- **路由**：Vue Router 4

---

## 项目结构

```
czyj/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/v1/            # API路由
│   │   │   ├── auth.py        # 认证接口
│   │   │   ├── schools.py     # 学校/班级接口
│   │   │   ├── tasks.py       # 任务接口
│   │   │   └── evaluations.py # 评价接口
│   │   ├── core/              # 核心模块
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库连接
│   │   │   ├── security.py    # 安全模块
│   │   │   ├── redis_client.py
│   │   │   └── storage.py     # MinIO存储
│   │   ├── models/            # 数据模型（22张表）
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务逻辑
│   │   └── utils/
│   │       └── compliance.py   # 合规工具
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt
│
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── api/               # API封装
│   │   ├── components/        # 组件
│   │   ├── layouts/           # 布局
│   │   │   ├── TeacherLayout.vue
│   │   │   └── ParentLayout.vue
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia状态
│   │   ├── styles/            # 样式
│   │   ├── utils/
│   │   │   ├── request.ts     # HTTP封装
│   │   │   └── compliance.ts  # 合规工具
│   │   └── views/             # 页面
│   │       ├── auth/          # 登录注册
│   │       ├── teacher/       # 教师端
│   │       └── parent/        # 家长端
│   └── package.json
│
├── docker-compose.yml          # Docker编排
├── nginx.conf                  # Nginx配置
└── README.md
```

---

## 核心功能

### 1. 认证系统
- 手机号 + 密码登录
- JWT访问令牌 + 刷新令牌
- 角色权限：超级管理员、学校管理员、教师、家长

### 2. 学校管理
- 学校注册与认证
- 年级班级管理
- 学生档案管理
- 家长绑定学生

### 3. 任务管理（教师端）
- 发布分层学习任务
- 任务分组（学习小组）
- 合规检查（违规词汇检测）
- 时长预警（每日60分钟上限）

### 4. 家长端
- 查看孩子学习建议（【选做】标记）
- 拍照记录任务完成
- 简短反馈提交
- 匿名化班级统计查看

### 5. 评价系统
- 多维度评价（星级、等级、布尔、分数、文本）
- 日常评价记录
- 成长档案生成

---

## 合规保障

### 违规词汇检测
系统自动检测以下违规词汇：
- 排名、排行榜 → 个人成长进度、班级分布概况
- 快慢班 → 学习小组
- 好差生 → 不同学习阶段的学生
- 打卡 → 记录
- 每日必做 → 选做建议
- 必须完成 → 建议完成

### 时长控制
- 所有任务标记为【选做】
- 单次任务建议时长 ≤ 60分钟
- 每日总时长预警 ≤ 60分钟

### 数据隐私
- 家长仅查看自己孩子数据
- 班级统计完全匿名化（约10%的同学、约半数同学等）

---

## 部署说明

### 开发环境（230服务器）
```bash
# 安装后端依赖
cd /home/code/czyj/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install

# 启动开发服务器
npm run dev
```

### 测试环境（81服务器）
```bash
# 启动所有服务
docker-compose up -d

# 访问地址
# 前端：http://20.20.30.81:8001
# 后端：http://20.20.30.81:8000
# MinIO控制台：http://20.20.30.81:9003
```

### 端口分配
| 服务 | 端口 |
|------|------|
| 前端 | 8001 |
| 后端 | 8000 |
| PostgreSQL | 5433 |
| Redis | 6380 |
| MinIO API | 9002 |
| MinIO Console | 9003 |

---

## 测试账号

- **验证码**：123456（测试环境固定）

---

## 后续开发建议

1. **完善前端页面**：班级详情、评价录入、数据分析等页面
2. **API完善**：图片上传、数据统计、消息通知等接口
3. **测试覆盖**：编写单元测试和集成测试
4. **性能优化**：缓存策略、数据库索引优化
5. **安全加固**：日志审计、请求限流、HTTPS配置

---

## 代码统计

- **总代码行数**：约4714行
- **文件数量**：45个（Python + TypeScript + Vue）
- **数据库表**：22张

---

**开发完成时间**：2026-05-10  
**版本**：v1.0.0-alpha
