#!/usr/bin/env python3
"""
EventPilot 前后端联调测试
验证前端通过代理访问后端API
"""

import requests
import json
import sys
from datetime import datetime

# 测试配置
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_success(message):
    print(f"✓ {message}")

def print_error(message):
    print(f"✗ {message}")

def test_frontend_direct():
    """测试前端首页"""
    print_section("1. 前端服务访问测试")
    try:
        response = requests.get(f"{FRONTEND_URL}/")
        if response.status_code == 200:
            print_success("前端服务响应正常")
            return True
        else:
            print_error(f"前端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"前端连接失败: {e}")
        return False

def test_api_proxy():
    """测试API代理"""
    print_section("2. 前端API代理测试")
    try:
        response = requests.get(f"{FRONTEND_URL}/api/")
        if response.status_code == 200:
            data = response.json()
            print_success("API代理工作正常")
            print(f"  API名称: {data.get('data',{}).get('name', 'unknown')}")
            print(f"  版本: {data.get('data',{}).get('version', 'unknown')}")
            return True
        else:
            print_error(f"API代理异常: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API代理连接失败: {e}")
        return False

def test_backend_direct():
    """直接测试后端"""
    print_section("3. 后端API直接测试")
    try:
        response = requests.get(f"{BACKEND_URL}/api/")
        if response.status_code == 200:
            data = response.json()
            print_success("后端服务响应正常")
            return True
        else:
            print_error(f"后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"后端连接失败: {e}")
        return False

def test_full_integration():
    """完整集成测试"""
    print_section("4. 完整集成测试")
    print("测试登录 -> 创建数据 -> 读取数据 流程")
    
    try:
        # 登录
        response = requests.post(f"{FRONTEND_URL}/api/users/auth/login/", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code in [200, 201]:
            data = response.json()
            token = data['data']['token']
            headers = {'Authorization': f'Bearer {token}'}
            print_success("登录成功")
            
            # 创建事件
            event_data = {
                "name": "集成测试事件",
                "type": "conference",
                "description": "前后端联调测试",
                "start_date": "2024-12-01T00:00:00Z",
                "end_date": "2024-12-02T00:00:00Z",
                "status": "planning"
            }
            
            response = requests.post(f"{FRONTEND_URL}/api/events/events/", json=event_data, headers=headers)
            if response.status_code in [200, 201]:
                print_success("事件创建成功")
                
                # 读取事件列表
                response = requests.get(f"{FRONTEND_URL}/api/events/events/", headers=headers)
                if response.status_code in [200, 201]:
                    events = response.json()
                    print_success(f"读取成功，共 {events.get('count', 0)} 个事件")
                    return True
                else:
                    print_error(f"读取失败: {response.status_code}")
                    return False
            else:
                print_error(f"事件创建失败: {response.status_code}")
                return False
        else:
            print_error(f"登录失败: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"集成测试失败: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  EventPilot 前后端联调测试")
    print("  开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = []
    
    # 测试1: 前端服务
    results.append(("前端服务", test_frontend_direct()))
    
    # 测试2: 后端服务
    results.append(("后端服务", test_backend_direct()))
    
    # 测试3: API代理
    results.append(("API代理", test_api_proxy()))
    
    # 测试4: 完整集成
    results.append(("完整集成", test_full_integration()))
    
    # 总结
    print_section("测试结果总结")
    print(f"  总测试数: {len(results)}")
    print(f"  通过数: {sum(1 for _, r in results if r)}")
    print(f"  失败数: {sum(1 for _, r in results if not r)}")
    print()
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name:20s} {status}")
    
    all_passed = all(r for _, r in results)
    print()
    if all_passed:
        print_success("所有测试通过！前后端联调验证成功")
        print_success("EventPilot系统已准备好进行进一步开发或部署")
    else:
        print_error("部分测试失败，需要进一步调试")
    
    print("="*60)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
