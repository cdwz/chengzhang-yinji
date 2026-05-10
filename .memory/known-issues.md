# 成长印记项目 - 已知问题与解决方案

## 2026-05-10: FastAPI 路由顺序冲突（关键！）

### 问题现象
- `GET /api/schools/classes` 返回 422 错误：`invalid UUID 'classes': length must be between 32..36 characters`
- `GET /api/students/groups` 返回 500 错误：`invalid UUID 'groups'`

### 根因分析
FastAPI 按定义顺序匹配路由。动态路由（如 `/{school_id}`）如果定义在静态路由（如 `/classes`）之前，会先匹配到动态路由，导致将静态路径字符串当作 UUID 参数解析。

### 错误示例
```python
# 错误顺序！
@router.get("/{school_id}")  # 动态路由在前
async def get_school(school_id: str): ...

@router.get("/classes")  # 静态路由在后 - 永远不会被匹配到！
async def list_classes(): ...
```

### 正确示例
```python
# 正确顺序！
@router.get("/classes")  # 静态路由在前
async def list_classes(): ...

@router.get("/{school_id}")  # 动态路由在后
async def get_school(school_id: str): ...
```

### 教训总结
- **静态路由必须在动态路由之前定义**
- 常见静态路由：`/classes`, `/groups`, `/import`, `/search`, `/regions`
- 常见动态路由：`/{id}`, `/{user_id}`, `/{school_id}`
- 受影响的文件：`schools.py`, `students.py`

---

## 2026-05-10: SQLAlchemy MissingGreenlet 错误

### 问题现象
创建班级时返回 500 错误，日志显示 `MissingGreenlet` 异常。

### 根因分析
异步 SQLAlchemy 在异步上下文中访问延迟加载的关系属性时会触发此错误。

### 解决方案
使用 `selectinload()` 预加载关系：
```python
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(School)
    .options(selectinload(School.grades))
    .where(School.id == school_id)
)
```

---

## 2026-05-10: Alembic URL 编码问题

### 问题现象
`alembic upgrade head` 报错：`invalid interpolation syntax in 'postgresql+asyncpg://...' at position 30`

### 根因分析
数据库URL中的 `%40`（编码后的@）被 configparser 误认为是插值语法。

### 解决方案
在 `alembic/env.py` 中转义 `%` 字符：
```python
db_url = settings.DATABASE_URL.replace('%', '%%')
config.set_main_option("sqlalchemy.url", db_url)
```

---

## 2026-05-10: Nginx API代理404问题

### 问题现象
通过 Nginx 代理（8001端口）访问后端API返回404，但直接访问后端（8000端口）正常。

### 根因分析
Nginx配置中 `proxy_pass http://czyj-backend:8000/;` 末尾的斜杠导致 `/api/` 路径被替换，请求 `/api/auth/send-code` 被转发为 `/auth/send-code`。

### 正确配置
```nginx
location /api/ {
    proxy_pass http://czyj-backend:8000;  # 末尾不加斜杠，保留/api前缀
}
```

### 教训总结
- `proxy_pass` 末尾斜杠会替换匹配的 location 路径
- Vue History 路由需要 `try_files $uri $uri/ /index.html;`
- 部署后必须同时测试前端路由和API代理

---

## 2026-05-10: 数据库密码URL编码问题

### 问题现象
后端容器启动后立即退出，日志显示数据库连接失败。

### 根因分析
密码中包含 `@` 符号，在数据库连接URL中被误解析为主机分隔符。

### 解决方案
密码中的特殊字符需要URL编码：`@` → `%40`
```
DATABASE_URL: postgresql+asyncpg://czyj:Czyj%402026Dev@postgres:5432/czyj_db
```

---

## Vue History路由404问题

### 问题现象
部署后访问页面首页正常，但直接访问子路由（如 /login）返回404。

### 根因分析
Vue Router 使用 History 模式，路由是虚拟路径，没有对应物理文件。Nginx 默认只响应真实存在的文件。

### 解决方案
Nginx 配置添加 try_files 回退：
```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 2026-05-10: 页面访问问题诊断记录

### 问题报告
用户报告访问 http://20.20.30.81:8001 及子路由无法正常打开页面。

### 诊断过程
1. 检查容器状态 → 所有容器正常运行
2. 检查index.html → 存在且内容正确
3. 检查assets目录 → 32个文件，主JS 1.4MB
4. 容器内部访问 → HTTP 200
5. 外部curl测试 → HTTP 200
6. Nginx配置 → 正确生效
7. API代理 → 正常工作

### 结论
系统完全正常，可能是浏览器缓存问题。

### 建议
- 清除浏览器缓存
- 强制刷新 (Ctrl+F5)
- 使用无痕模式测试

---

## 2026-05-10: 前端路由404问题

### 问题现象
浏览器访问首页显示"404 页面不存在"，但页面标题正确显示"成长印记"。

### 根因分析
Vue Router 配置中缺少根路径 `/` 的路由定义，导致直接匹配到 `/:pathMatch(.*)*` 404路由。

### 解决方案
在路由配置开头添加：
```typescript
{
  path: '/',
  redirect: '/login'
}
```

### 验证方法
1. 检查 curl 返回的 HTML 不包含 "页面不存在"
2. 浏览器刷新后应自动跳转到登录页

### 注意事项
Vue SPA 的路由匹配在浏览器端完成，服务端只返回 index.html。用户需要刷新浏览器加载新的 JS 文件。
