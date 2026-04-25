#!/bin/bash
# EventPilot API测试脚本

BASE_URL="http://172.28.166.164:8000/api"
echo "=== EventPilot API测试 ==="
echo ""

# 登录
echo "1. 测试登录API..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

# 提取token（简单方法：grep token后的字符串）
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
echo "提取的token: ${TOKEN:0:50}..."
echo ""

# 测试各个API端点
echo "2. 测试任务列表API..."
curl -s $BASE_URL/tasks/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "3. 测试活动列表API..."
curl -s $BASE_URL/events/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "4. 测试用户列表API..."
curl -s $BASE_URL/users/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "5. 测试检查清单API..."
curl -s $BASE_URL/checklists/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "6. 测试文件API..."
curl -s $BASE_URL/files/ -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "=== API测试完成 ==="
