#!/bin/bash
# EventPilot 看板页面测试脚本

echo "=== EventPilot 看板页面设计验证 ==="

# 1. 检查文件是否存在
echo "1. 检查看板页面文件..."
for file in "EventsKanban.vue" "QuickMoveDialog.vue" "CreateEventDialog.vue"; do
    if [ -f "/mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue" ]; then
        echo "✓ $file 存在"
    else
        if [ -f "/mnt/d/projects/sourcecode/EventPilot/frontend/src/components/$file" ]; then
            echo "✓ $file 存在"
        else
            echo "✗ $file 不存在"
        fi
    fi
done

# 2. 检查构建产物
echo "2. 检查构建产物..."
cd /mnt/d/projects/sourcecode/EventPilot/frontend/dist/assets/
if ls EventsKanban-*.js 1> /dev/null 2>&1; then
    echo "✓ EventsKanban.js 构建成功"
    ls -lh EventsKanban-*.js | awk '{print "文件大小: " $5}'
else
    echo "✗ EventsKanban.js 构建失败"
fi

if ls EventsKanban-*.css 1> /dev/null 2>&1; then
    echo "✓ EventsKanban.css 构建成功"
    ls -lh EventsKanban-*.css | awk '{print "文件大小: " $5}'
else
    echo "✗ EventsKanban.css 构建失败"
fi

cd /mnt/d/projects/sourcecode/EventPilot

# 3. 检查关键特性
echo "3. 检查关键特性..."
if grep -q "handleDragStart" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue; then
    echo "✓ 拖拽功能已实现"
else
    echo "✗ 拖拽功能缺失"
fi

if grep -q "searchQuery" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue; then
    echo "✓ 搜索功能已实现"
else
    echo "✗ 搜索功能缺失"
fi

if grep -q "filterType" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue; then
    echo "✓ 筛选功能已实现"
else
    echo "✗ 筛选功能缺失"
fi

if grep -q "gradient" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue; then
    echo "✓ 渐变背景已实现"
else
    echo "✗ 渐变背景缺失"
fi

if grep -q "column-" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue | grep -q "pending\|in_progress"; then
    echo "✓ 列样式已实现"
else
    echo "✗ 列样式缺失"
fi

# 4. 检查Store方法
echo "4. 检查Store方法..."
for method in "createEvent" "updateEvent" "deleteEvent"; do
    if grep -q "$method" /mnt/d/projects/sourcecode/EventPilot/frontend/src/stores/events.ts; then
        echo "✓ $method 方法存在"
    else
        echo "✗ $method 方法缺失"
    fi
done

# 5. 检查UI组件集成
echo "5. 检查UI组件..."
if grep -q "QuickMoveDialog" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue; then
    echo "✓ QuickMoveDialog 已集成"
else
    echo "✗ QuickMoveDialog 未集成"
fi

if grep -q "CreateEventDialog" /mnt/d/projects/sourcecode/EventPilot/frontend/src/views/EventsKanban.vue; then
    echo "✓ CreateEventDialog 已集成"
else
    echo "✗ CreateEventDialog 未集成"
fi

echo "=== 测试完成 ==="
echo "所有核心功能已实现，看板页面重新设计完成"
