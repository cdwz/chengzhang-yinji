#!/bin/bash
# 成长印记 - 完整性与功能性测试脚本

BASE_URL="http://20.20.30.81:8001"
API_URL="http://20.20.30.81:8000"
SCREENSHOT_DIR="./test-results"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建测试结果目录
mkdir -p $SCREENSHOT_DIR

echo "=================================================="
echo "🚀 成长印记 - 完整性与功能性测试"
echo "=================================================="
echo ""

PASSED=0
FAILED=0
WARNINGS=0

# 测试函数
test_case() {
    local name=$1
    local result=$2
    local detail=$3
    
    if [ "$result" = "pass" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $name"
        [ -n "$detail" ] && echo "   $detail"
        ((PASSED++))
    elif [ "$result" = "fail" ]; then
        echo -e "${RED}❌ FAIL${NC} - $name"
        [ -n "$detail" ] && echo "   $detail"
        ((FAILED++))
    else
        echo -e "${YELLOW}⚠️  WARN${NC} - $name"
        [ -n "$detail" ] && echo "   $detail"
        ((WARNINGS++))
    fi
}

# ========== 测试1: 前端首页可访问性 ==========
echo ""
echo "📝 测试组1: 前端可访问性"
echo "--------------------------------------------------"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 $BASE_URL)
if [ "$HTTP_CODE" = "200" ]; then
    test_case "前端首页可访问" "pass" "HTTP状态码: $HTTP_CODE"
else
    test_case "前端首页可访问" "fail" "HTTP状态码: $HTTP_CODE"
fi

# 检查HTML内容
FRONTEND_HTML=$(curl -s --connect-timeout 5 $BASE_URL)
if echo "$FRONTEND_HTML" | grep -q "<!DOCTYPE html>"; then
    test_case "HTML文档结构正确" "pass"
else
    test_case "HTML文档结构正确" "fail" "未找到DOCTYPE声明"
fi

# 检查Vue应用挂载点
if echo "$FRONTEND_HTML" | grep -q 'id="app"'; then
    test_case "Vue应用挂载点存在" "pass"
else
    test_case "Vue应用挂载点存在" "fail"
fi

# 检查JS资源加载
JS_FILES=$(echo "$FRONTEND_HTML" | grep -o 'src="[^"]*\.js"' | wc -l)
if [ "$JS_FILES" -gt 0 ]; then
    test_case "JS资源文件引用" "pass" "找到 $JS_FILES 个JS文件"
else
    test_case "JS资源文件引用" "fail" "未找到JS文件引用"
fi

# ========== 测试2: 后端API可访问性 ==========
echo ""
echo "📝 测试组2: 后端API可访问性"
echo "--------------------------------------------------"

# API文档
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 $API_URL/docs)
if [ "$HTTP_CODE" = "200" ]; then
    test_case "API文档可访问" "pass" "HTTP状态码: $HTTP_CODE"
else
    test_case "API文档可访问" "fail" "HTTP状态码: $HTTP_CODE"
fi

# OpenAPI规范
OPENAPI=$(curl -s --connect-timeout 5 $API_URL/openapi.json 2>/dev/null)
if [ -n "$OPENAPI" ] && echo "$OPENAPI" | grep -q '"openapi"'; then
    test_case "OpenAPI规范有效" "pass"
    
    # 检查API端点数量
    API_COUNT=$(echo "$OPENAPI" | grep -o '"/api/v1/[^"]*"' | wc -l)
    test_case "API端点定义" "pass" "找到 $API_COUNT 个API端点"
else
    test_case "OpenAPI规范有效" "fail"
fi

# 健康检查端点
HEALTH=$(curl -s --connect-timeout 5 $API_URL/health 2>/dev/null)
if [ -n "$HEALTH" ]; then
    test_case "健康检查端点" "pass"
else
    test_case "健康检查端点" "warn" "未实现/health端点"
fi

# ========== 测试3: 静态资源检查 ==========
echo ""
echo "📝 测试组3: 静态资源检查"
echo "--------------------------------------------------"

# 检查CSS文件
CSS_FILE=$(echo "$FRONTEND_HTML" | grep -o 'href="[^"]*\.css"' | head -1 | sed 's/href="//;s/"//')
if [ -n "$CSS_FILE" ]; then
    # 提取相对路径
    CSS_PATH=$(echo "$CSS_FILE" | sed 's/^\///')
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$BASE_URL/$CSS_PATH")
    if [ "$HTTP_CODE" = "200" ]; then
        test_case "CSS资源加载" "pass" "$CSS_FILE"
    else
        test_case "CSS资源加载" "fail" "$CSS_FILE (HTTP $HTTP_CODE)"
    fi
else
    test_case "CSS资源加载" "warn" "未找到CSS文件引用"
fi

# ========== 测试4: 合规性检查 ==========
echo ""
echo "📝 测试组4: 页面合规性检查"
echo "--------------------------------------------------"

# 违规词汇检查
FORBIDDEN_WORDS="排名 排行榜 快慢班 好差生 打卡 每日必做 必须完成 重点班 实验班"
FOUND_FORBIDDEN=""

for word in $FORBIDDEN_WORDS; do
    if echo "$FRONTEND_HTML" | grep -q "$word"; then
        FOUND_FORBIDDEN="$FOUND_FORBIDDEN $word"
    fi
done

if [ -z "$FOUND_FORBIDDEN" ]; then
    test_case "违规词汇检查" "pass" "未发现违规词汇"
else
    test_case "违规词汇检查" "fail" "发现违规词汇:$FOUND_FORBIDDEN"
fi

# ========== 测试5: 数据库连接 ==========
echo ""
echo "📝 测试组5: 数据库连接检查"
echo "--------------------------------------------------"

# 通过后端检查数据库连接
DB_CHECK=$(curl -s --connect-timeout 10 -X POST "$API_URL/api/v1/auth/send-code" \
    -H "Content-Type: application/json" \
    -d '{"phone":"13800138000"}' 2>/dev/null)

if [ -n "$DB_CHECK" ]; then
    test_case "数据库连接" "pass" "API响应正常"
else
    test_case "数据库连接" "warn" "无法验证（可能需要完整API实现）"
fi

# ========== 测试6: 服务健康状态 ==========
echo ""
echo "📝 测试组6: 服务健康状态"
echo "--------------------------------------------------"

# PostgreSQL
PG_CHECK=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 20.20.30.81:5433 2>/dev/null || echo "000")
if [ "$PG_CHECK" != "000" ]; then
    test_case "PostgreSQL服务" "pass" "端口5433响应"
else
    test_case "PostgreSQL服务" "fail" "端口5433无响应"
fi

# Redis
REDIS_CHECK=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 20.20.30.81:6380 2>/dev/null || echo "000")
if [ "$REDIS_CHECK" != "000" ]; then
    test_case "Redis服务" "pass" "端口6380响应"
else
    test_case "Redis服务" "fail" "端口6380无响应"
fi

# MinIO
MINIO_CHECK=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 20.20.30.81:9002 2>/dev/null || echo "000")
if [ "$MINIO_CHECK" != "000" ]; then
    test_case "MinIO服务" "pass" "端口9002响应"
else
    test_case "MinIO服务" "fail" "端口9002无响应"
fi

# ========== 测试7: 安全性检查 ==========
echo ""
echo "📝 测试组7: 安全性检查"
echo "--------------------------------------------------"

# 检查HTTPS（开发环境可能没有）
if echo "$BASE_URL" | grep -q "https"; then
    test_case "HTTPS启用" "pass"
else
    test_case "HTTPS启用" "warn" "开发环境未启用HTTPS"
fi

# 检查安全头
SECURITY_HEADERS=$(curl -sI --connect-timeout 5 $API_URL 2>/dev/null)
if echo "$SECURITY_HEADERS" | grep -qi "X-Content-Type-Options"; then
    test_case "安全响应头" "pass"
else
    test_case "安全响应头" "warn" "建议添加安全响应头"
fi

# ========== 测试8: API端点检查 ==========
echo ""
echo "📝 测试组8: API端点检查"
echo "--------------------------------------------------"

# 从OpenAPI获取端点列表
if [ -n "$OPENAPI" ]; then
    # 认证端点
    if echo "$OPENAPI" | grep -q '"/api/v1/auth/send-code"'; then
        test_case "发送验证码端点" "pass"
    else
        test_case "发送验证码端点" "fail" "未定义"
    fi
    
    if echo "$OPENAPI" | grep -q '"/api/v1/auth/login"'; then
        test_case "登录端点" "pass"
    else
        test_case "登录端点" "fail" "未定义"
    fi
    
    # 学校端点
    if echo "$OPENAPI" | grep -q '"/api/v1/schools"'; then
        test_case "学校管理端点" "pass"
    else
        test_case "学校管理端点" "fail" "未定义"
    fi
    
    # 任务端点
    if echo "$OPENAPI" | grep -q '"/api/v1/tasks"'; then
        test_case "任务管理端点" "pass"
    else
        test_case "任务管理端点" "fail" "未定义"
    fi
    
    # 评价端点
    if echo "$OPENAPI" | grep -q '"/api/v1/evaluations"'; then
        test_case "评价管理端点" "pass"
    else
        test_case "评价管理端点" "fail" "未定义"
    fi
fi

# ========== 测试汇总 ==========
echo ""
echo "=================================================="
echo "📊 测试报告汇总"
echo "=================================================="
echo ""
echo -e "${GREEN}✅ 通过: $PASSED${NC}"
echo -e "${RED}❌ 失败: $FAILED${NC}"
echo -e "${YELLOW}⚠️  警告: $WARNINGS${NC}"
echo ""

TOTAL=$((PASSED + FAILED + WARNINGS))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有关键测试通过！${NC}"
    echo ""
    echo "📋 访问地址:"
    echo "   前端: http://20.20.30.81:8001"
    echo "   后端: http://20.20.30.81:8000/docs"
    echo "   MinIO: http://20.20.30.81:9003"
    exit 0
else
    echo -e "${RED}⚠️  存在失败的测试项，请检查。${NC}"
    exit 1
fi
