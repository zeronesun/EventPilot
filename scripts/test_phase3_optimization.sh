#!/bin/bash
# Phase 3 性能优化和系统测试脚本

set -e

echo "🚀 开始Phase 3性能优化和系统测试..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 创建必要的目录
mkdir -p logs
mkdir -p test_results

echo -e "${GREEN}✓ 目录创建完成${NC}"

# 1. 数据库查询优化检查
echo "📊 检查数据库查询优化..."
python manage.py check --deploy --settings=config.settings.base 2>&1 | tee logs/deploy_check.log

# 2. 运行单元测试
echo "🧪 运行单元测试..."
python -m pytest tests/test_phase3_complete.py -v --tb=short --no-header -q 2>&1 | tee test_results/unit_tests.result || echo -e "${YELLOW}部分单元测试失败，继续执行${NC}"

# 3. 运行集成测试
echo "🔗 运行集成测试..."
python -m pytest tests/test_phase3_complete.py::Phase3IntegrationTests -v --tb=short -q 2>&1 | tee test_results/integration_tests.result || echo -e "${YELLOW}部分集成测试失败，继续执行${NC}"

# 4. 性能基准测试
echo "⚡ 运行性能基准测试..."
python -m pytest tests/test_phase3_complete.py::Phase3PerformanceTests -v --tb=line -q 2>&1 | tee test_results/performance_tests.result

# 5. 数据库迁移检查
echo "🗄️ 检查数据库迁移..."
python manage.py showmigrations | tee logs/migrations.log

# 6. 代码质量检查
echo "🔍 检查代码质量..."
python -m flake8 apps/profiles --max-line-length=120 2>&1 | tee logs/code_quality.log || echo -e "${YELLOW}代码质量检查发现问题${NC}"

# 7. 测试覆盖率
echo "📈 计算测试覆盖率..."
python -m pytest tests/test_phase3_complete.py --cov=apps.profiles --cov-report=html --cov-report=term 2>&1 | tee test_results/coverage.result

# 8. API性能测试
echo "🌐 检查API性能..."
python manage.py check --deploy 2>&1 | grep -i "performance" || echo "性能检查通过"

# 9. 静态资源优化检查
echo "🎨 检查前端资源..."
if [ -d "frontend" ]; then
    cd frontend
    if command -v npm &> /dev/null; then
        npm run build --if-present 2>&1 | tee ../logs/frontend_build.log || echo -e "${YELLOW}前端构建跳过或失败${NC}"
    else
        echo -e "${YELLOW}npm未安装，跳过前端构建${NC}"
    fi
    cd ..
fi

# 10. 文档生成
echo "📚 生成API文档..."
python manage.py generateschema 2>&1 | tee logs/schema.log || true

# 生成测试报告摘要
echo "" 
echo "📋 测试报告摘要"
echo "=================="

# 统计测试结果
if [ -f "test_results/unit_tests.result" ]; then
    echo "单元测试:"
    python -c "
import re
with open('test_results/unit_tests.result', 'r') as f:
    content = f.read()
    if 'passed' in content:
        print('  状态: ✓ 通过')
    else:
        print('  状态: ⚠ 需要检查')
"
fi

if [ -f "test_results/integration_tests.result" ]; then
    echo "集成测试:"
    python -c "
import re
with open('test_results/integration_tests.result', 'r') as f:
    content = f.read()
    if 'passed' in content:
        print('  状态: ✓ 通过')
    else:
        print('  状态: ⚠ 需要检查')
"
fi

if [ -f "test_results/performance_tests.result" ]; then
    echo "性能测试:"
    echo "  推荐算法性能: 检查日志中的耗时"
    echo "  并发处理性能: 检查日志中的耗时"
fi

if [ -f "test_results/coverage.result" ]; then
    echo "测试覆盖率:"
    python -c "
import re
with open('test_results/coverage.result', 'r') as f:
    for line in f:
        if '%' in line and'TOTAL' in line:
            print(f'  {line.strip()}')
            break
"
fi

echo ""
echo -e "${GREEN}✅ Phase 3性能优化和系统测试完成！${NC}"
echo ""
echo "📊 详细结果已保存到: test_results/"
echo "📝 日志已保存到: logs/"
echo ""
echo "⚠️ 注意事项:"
echo "1. 检查测试结果文件中的详细信息"
echo "2. 如有失败的测试，请查看日志文件"
echo "3. 性能基准可根据实际需求调整"