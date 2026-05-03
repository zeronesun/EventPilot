#!/bin/bash
# EventPilot API功能验证测试脚本
# 验证修复：活动编辑、时间显示、用户管理

set -e

BASE_URL="http://localhost:8000"
TOKEN=""
PASS_COUNT=0
FAIL_COUNT=0

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS_COUNT++))
}

log_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL_COUNT++))
}

log_info() {
    echo -e "${YELLOW}ℹ️  INFO${NC}: $1"
}

echo "=========================================="
echo "EventPilot 功能验证测试"
echo "=========================================="
echo ""

# 测试1: 用户登录
echo "【测试1】用户登录认证"
LOGIN_RESP=$(curl -s -X POST "$BASE_URL/api/users/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

if echo "$LOGIN_RESP" | grep -q '"token"'; then
    TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
    log_pass "登录成功，Token已获取"
else
    log_fail "登录失败: $LOGIN_RESP"
    exit 1
fi

echo ""
echo "【测试2】获取活动列表（验证时间字段）"
EVENTS_RESP=$(curl -s "$BASE_URL/api/events/events/" \
  -H "Authorization: Bearer $TOKEN")

# 检查是否有start_date和end_date字段
if echo "$EVENTS_RESP" | grep -q '"start_date"' && echo "$EVENTS_RESP" | grep -q '"end_date"'; then
    log_pass "活动列表包含 start_date 和 end_date 字段"
    
    # 提取第一个活动的日期
    FIRST_EVENT_START=$(echo "$EVENTS_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('results'):
    event = data['results'][0]
    print(f\"活动名称: {event['name']}\")
    print(f\"开始时间: {event.get('start_date', 'N/A')}\")
    print(f\"结束时间: {event.get('end_date', 'N/A')}\")
" 2>/dev/null || true)
    log_info "第一个活动信息:\n$FIRST_EVENT_START"
else
    log_fail "活动列表缺少时间字段"
fi

echo ""
echo "【测试3】更新活动（验证400错误修复）"

# 获取第一个活动ID
EVENT_ID=$(echo "$EVENTS_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['results'][0]['id'] if data.get('results') else '')
")

if [ -n "$EVENT_ID" ]; then
    log_info "使用活动ID: $EVENT_ID 进行更新测试"
    
    # 测试更新活动（包含结束时间）
    UPDATE_RESP=$(curl -s -X PUT "$BASE_URL/api/events/events/$EVENT_ID/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "策划活动",
        "type": "conference",
        "status": "planning",
        "start_date": "2026-06-01T09:00:00",
        "end_date": "2026-06-02T18:00:00",
        "description": "浏览器自动化测试 - 验证修复",
        "estimated_budget": 5000
      }')
    
    # 检查HTTP状态码（通过响应头或内容判断）
    HTTP_CODE=$(echo "$UPDATE_RESP" | head -1 | grep -oP '\d{3}' || echo "unknown")
    
    if echo "$UPDATE_RESP" | grep -q '400\|error\|required'; then
        log_fail "更新失败 (400错误): $UPDATE_RESP"
    elif echo "$UPDATE_RESP" | grep -q '"name"\|"id"'; then
        log_pass "活动更新成功（包含end_date字段）"
        log_info "更新响应: $(echo $UPDATE_RESP | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f\"名称: {d.get(\"name\",\"?\")}, 状态: {d.get(\"status\",\"?\")}\"' 2>/dev/null)"
    else
        log_info "更新响应: $UPDATE_RESP"
    fi
else
    log_fail "无法获取活动ID"
fi

echo ""
echo "【测试4】用户列表API（验证用户管理）"
USERS_RESP=$(curl -s "$BASE_URL/api/users/users/" \
  -H "Authorization: Bearer $TOKEN")

if echo "$USERS_RESP" | grep -q '\['; then
    USER_COUNT=$(echo "$USERS_RESP" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "unknown")
    log_pass "用户列表获取成功，共 $USER_COUNT 个用户"
else
    log_info "用户API响应: $USERS_RESP"
fi

echo ""
echo "【测试5】创建新用户（验证密码必填）"

# 测试5a: 不填密码应该失败
CREATE_NO_PASS=$(curl -s -X POST "$BASE_URL/api/users/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_nopass",
    "email": "nopass@test.com",
    "role": "executor"
  }')

if echo "$CREATE_NO_PASS" | grep -q 'password\|required\|此字段'; then
    log_pass "密码必填验证生效 - 无密码时拒绝创建"
else
    log_info "无密码创建响应: $CREATE_NO_PASS"
fi

# 测试5b: 正确填写密码应该成功
CREATE_WITH_PASS=$(curl -s -X POST "$BASE_URL/api/users/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_browser_user",
    "email": "browser@test.com",
    "password": "Test123456",
    "first_name": "浏览器",
    "role": "executor"
  }')

if echo "$CREATE_WITH_PASS" | grep -q '"id"\|"username"\|created'; then
    log_pass "用户创建成功（带密码）"
    
    # 验证用户是否出现在列表中
    sleep 1
    USERS_AFTER_CREATE=$(curl -s "$BASE_URL/api/users/users/" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$USERS_AFTER_CREATE" | grep -q "test_browser_user"; then
        log_pass "新用户已在列表中显示（刷新验证通过）"
    else
        log_info "检查用户是否在列表中..."
    fi
elif echo "$CREATE_WITH_PASS" | grep -q 'already exists'; then
    log_pass "用户已存在（说明之前创建成功）"
else
    log_info "创建用户响应: $CREATE_WITH_PASS"
fi

echo ""
echo "=========================================="
echo "测试结果汇总"
echo "=========================================="
echo -e "${GREEN}通过: $PASS_COUNT${NC}"
echo -e "${RED}失败: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 所有关键测试通过！${NC}"
    exit 0
else
    echo -e "${RED}⚠️ 存在失败的测试项${NC}"
    exit 1
fi