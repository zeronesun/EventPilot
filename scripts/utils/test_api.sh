#!/bin/bash
# 测试EventPilot API

echo "=== 测试1: 登录API ==="
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
echo "登录响应: $LOGIN_RESPONSE"

# 提取token
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('token',''))" 2>/dev/null)
echo "Token: ${TOKEN:0:50}..."

echo ""
echo "=== 测试2: 获取活动列表 ==="
EVENTS_RESPONSE=$(curl -s http://localhost:8000/api/events/events/ \
  -H "Authorization: Bearer $TOKEN")
echo "活动列表 (前500字符): ${EVENTS_RESPONSE:0:500}"

echo ""
echo "=== 测试3: 获取第一个活动详情 ==="
FIRST_EVENT_ID=$(echo $EVENTS_RESPONSE | python3 -c "import sys,json; data=json.load(sys.stdin); print(data['data'][0]['id'] if data.get('data') else 'None')" 2>/dev/null)
echo "第一个活动ID: $FIRST_EVENT_ID"

if [ "$FIRST_EVENT_ID" != "None" ] && [ -n "$FIRST_EVENT_ID" ]; then
  echo ""
  echo "=== 测试4: 更新活动（包含结束时间）==="
  UPDATE_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/events/events/$FIRST_EVENT_ID/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "测试活动",
      "type": "conference",
      "status": "planning",
      "start_date": "2026-06-01T09:00:00",
      "end_date": "2026-06-02T18:00:00",
      "description": "浏览器测试修复验证",
      "estimated_budget": 1000
    }')
  echo "更新响应: $UPDATE_RESPONSE"
  
  # 检查是否成功
  UPDATE_STATUS=$(echo $UPDATE_RESPONSE | python3 -c "import sys,json; print('SUCCESS' if '200' in str(json.load(sys.stdin)) or 'error' not in str(json.load(sys.stdin)).lower() or 'message' in str(json.load(sys.stdin)).lower() else 'FAILED')" 2>/dev/null)
  echo "更新状态: $UPDATE_STATUS"
fi

echo ""
echo "=== 测试5: 获取用户列表 ==="
USERS_RESPONSE=$(curl -s http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $TOKEN")
echo "用户列表 (前300字符): ${USERS_RESPONSE:0:300}"

echo ""
echo "=== 测试完成 ==="