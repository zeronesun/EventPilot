#!/usr/bin/env python3
"""
EventPilot 自动化功能审计工具
扫描所有Vue文件，提取按钮和交互元素
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set
import json

class VueComponentAuditor:
    """审计Vue组件中的交互元素"""

    def __init__(self, frontend_src_dir: str):
        self.frontend_src_dir = Path(frontend_src_dir)
        self.findings = {}

        # 常见的Element Plus按钮类和HTML按钮类
        self.button_patterns = [
            r'<el-button[^>]*>([^<]+)</el-button>',  # Element Plus按钮
            r'<button[^>]*>([^<]+)</button>',  # 原生button
            r'@click\s*=\s*["\']([^"\']+)["\']',  # 点击事件
            r'v-on:click\s*=\s*["\']([^"\']+)["\']',  # v-on:click
        ]

        # 常见的输入元素
        self.input_patterns = [
            r'<el-input[^>]*>',  # Element Plus输入框
            r'<input[^>]+>',  # 原生input
            r'<el-select[^>]*>',  # Element Plus下拉选择
            r'<el-checkbox[^>]*>',  # Element Plus复选框
            r'<el-radio[^>]*>',  # Element Plus单选
            r'<el-date-picker[^>]*>',  # Element Plus日期选择
        ]

        # 常见的表格操作
        self.table_patterns = [
            r'<el-table[^>]*>',  # Element Plus表格
            r':data\s*=\s*["\']([^"\']+)["\']',  # 表格数据绑定
        ]

        # 路由链接
        self.router_patterns = [
            r'<router-link[^>]*to\s*=\s*["\']([^"\']+)["\'][^>]*>([^<]+)</router-link>',
            r'\$router\.push\(["\']([^"\']+)["\']\)',
            r'\$router\.go\((-?\d+)\)',
        ]

    def audit_file(self, file_path: Path) -> Dict:
        """审计单个Vue文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        findings = {
            'file': str(file_path),
            'buttons': [],
            'inputs': [],
            'tables': [],
            'router_actions': [],
            'methods': [],
            'computed': [],
        }

        # 提取所有 @click 事件
        click_events = re.findall(r'@click\s*=\s*["\']([^"\']+)["\']', content)
        findings['buttons'].extend(click_events)

        # 提取所有方法定义
        methods_match = re.search(r'methods:\s*\{([^}]+)\}', content, re.DOTALL)
        if methods_match:
            methods_content = methods_match.group(1)
            method_names = re.findall(r'(\w+)\s*(?:\(|:)', methods_content)
            findings['methods'] = method_names

        # 提取所有computed属性
        computed_match = re.search(r'computed:\s*\{([^}]+)\}', content, re.DOTALL)
        if computed_match:
            computed_content = computed_match.group(1)
            computed_names = re.findall(r'(\w+)\s*(?:\(|:)', computed_content)
            findings['computed'] = computed_names

        # 提取所有 el-table 元素（用于识别表格）
        tables = re.findall(r'<el-table[^>]*>', content)
        findings['tables'] = len(tables)

        # 提取所有 el- 表单元素
        form_elements = re.findall(r'<el-(input|select|checkbox|radio|date-picker)[^>]*>', content)
        findings['inputs'] = len(form_elements)

        # 提取路由操作
        router_pushes = re.findall(r'\$router\.push\(["\']([^"\']+)["\']\)', content)
        findings['router_actions'] = router_pushes

        return findings

    def audit_all(self) -> Dict:
        """审计所有Vue组件"""
        views_dir = self.frontend_src_dir / 'views'
        components_dir = self.frontend_src_dir / 'components'

        all_findings = {}

        # 审计所有页面文件
        if views_dir.exists():
            for vue_file in views_dir.glob('*.vue'):
                page_name = vue_file.stem
                all_findings[f'page:{page_name}'] = self.audit_file(vue_file)

        # 审计所有组件文件
        if components_dir.exists():
            for vue_file in components_dir.glob('*.vue'):
                component_name = vue_file.stem
                all_findings[f'component:{component_name}'] = self.audit_file(vue_file)

        return all_findings

    def print_summary(self):
        """打印审计摘要"""
        findings = self.audit_all()

        print("="*80)
        print("EventPilot Vue组件功能审计报告")
        print("="*80)

        total_buttons = 0
        total_inputs = 0
        total_tables = 0
        total_methods = 0

        for key, value in findings.items():
            print(f"\n{key}:")
            print(f"  - 按钮事件: {len(value['buttons'])}")
            if value['buttons']:
                for btn in value['buttons'][:5]:  # 只显示前5个
                    print(f"      · {btn}")
                if len(value['buttons']) > 5:
                    print(f"      ... 还有 {len(value['buttons']) - 5} 个")

            print(f"  - 表单元素: {value['inputs']}")
            print(f"  - 表格: {value['tables']}")
            print(f"  - 方法: {len(value['methods'])}")
            if value['methods']:
                for method in value['methods']:
                    print(f"      · {method}()")

            print(f"  - 计算属性: {len(value['computed'])}")
            print(f"  - 路由操作: {len(value['router_actions'])}")

            total_buttons += len(value['buttons'])
            total_inputs += value['inputs']
            total_tables += value['tables']
            total_methods += len(value['methods'])

        print("\n" + "="*80)
        print("总计:")
        print(f"  - 按钮/点击事件: {total_buttons}")
        print(f"  - 表单元素: {total_inputs}")
        print(f"  - 表格: {total_tables}")
        print(f"  - 方法: {total_methods}")
        print("="*80)

        # 保存完整报告
        output_file = Path('/mnt/d/projects/sourcecode/EventPilot/devdoc/VUE_AUDIT_REPORT.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(findings, f, ensure_ascii=False, indent=2)

        print(f"\n完整报告已保存到: {output_file}")

if __name__ == '__main__':
    auditor = VueComponentAuditor('/mnt/d/projects/sourcecode/EventPilot/frontend/src')
    auditor.print_summary()
