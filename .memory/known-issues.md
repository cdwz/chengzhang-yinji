# 成长印记项目 - 已知问题与解决方案

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
