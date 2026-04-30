#!/bin/bash

# EventPilot 前端环境setup脚本
# 解决依赖问题和构建错误

echo "🔧 开始EventPilot前端环境setup..."

# 清理node_modules和缓存
echo "🧹 清理旧的node_modules..."
rm -rf node_modules
rm -rf package-lock.json
rm -rf .vite

# 重新安装依赖
echo "📦 安装依赖..."
npm install

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p .cache

echo "✅ 环境setup完成！"
echo ""
echo "🚀 你可以运行以下命令启动开发服务器:"
echo "   npm run dev"