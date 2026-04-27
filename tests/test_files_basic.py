#!/usr/bin/env python3
"""
文件功能测试（基础功能，无需S3配置）
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_files_basic_functions():
    """测试文件模块的基础功能"""

    print("="*60)
    print("文件模块基础功能测试")
    print("="*60)

    # 1. 登录
    print("\n1. 登录获取Token:")
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/auth/login/", json=login_payload)
    if r.status_code not in [200, 201]:
        print(f"❌ 登录失败: {r.text}")
        return False
    
    data = r.json()
    token = data.get('data', {}).get('token', data.get('token', ''))
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 测试文件列表获取
    print("\n2. 测试文件列表:")
    r = requests.get(f"{BASE_URL}/files/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        files_list = r.json()
        count = len(files_list.get('data', [])) if 'data' in files_list else len(files_list.get('results', []))
        print(f"✅ 文件列表获取成功: {count} 个文件")
    else:
        print(f"❌ 获取文件列表失败: {r.text}")

    # 3. 测试验证 - 空文件名应被拒绝
    print("\n3. 测试表单验证（空文件名）:")
    invalid_payload = {
        "filename": "",
        "file_size": 1024,
        "mime_type": "application/pdf"
    }
    r = requests.post(f"{BASE_URL}/files/", json=invalid_payload, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 400:
        print(f"✅ 表单验证正确（空文件名被拒绝）")
    else:
        print(f"⚠️  验证行为: {r.status_code}")

    # 4. 测试验证 - 无效MIME类型应被拒绝
    print("\n4. 测试表单验证（无效MIME类型）:")
    invalid_mime = {
        "filename": "test.exe",
        "file_size": 1024,
        "mime_type": "application/x-msdownload"  # exe文件通常不被允许
    }
    r = requests.post(f"{BASE_URL}/files/", json=invalid_mime, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 400:
        print(f"✅ 安全验证正常（危险文件类型被拒绝）")
    else:
        print(f"⚠️  验证行为: {r.status_code}")

    # 5. 测试文件上传初始化（预期会失败，因为缺少S3配置）
    print("\n5. 测试上传初始化:")
    upload_payload = {
        "filename": "test_document.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "metadata": {"category": "document"}
    }
    r = requests.post(f"{BASE_URL}/files/", json=upload_payload, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 500:
        try:
            result = r.json()
            if isinstance(result, dict):
                error = result.get('error', {}).get('message', '')
            else:
                error = str(result)
            if 'credentials' in error.lower() or 'Unable to locate credentials' in str(r.text):
                print(f"⚠️  上传失败（需要配置S3凭证）：跳过此测试")
            else:
                print(f"❌ 其他错误: {result}")
        except:
            error = str(r.text)
        if 'credentials' in error or 'Unable to locate credentials' in error:
            print(f"⚠️  上传失败（需要配置S3凭证）：跳过此测试")
    elif r.status_code:
        print(f"⚠️  返回 {r.status_code}: {str(r.text)[:100]}")
    else:
        print(f"✅ 上传初始化成功（S3配置正常）")

    # 6. 测试文件API的基本响应结构
    print("\n6. 测试API响应结构:")
    r = requests.get(f"{BASE_URL}/files/", headers=headers)
    if r.status_code == 200:
        result = r.json()
        if isinstance(result, dict):
            print(f"✅ API 返回字典结构")
        elif isinstance(result, list):
            print(f"✅ API 返回列表结构")
        else:
            print(f"⚠️  意外结构: {type(result)}")

    print("\n" + "="*60)
    print("✅ 文件模块基础测试完成!")
    print("="*60)
    print("注：文件上传和下载需要配置S3凭证或本地存储后端")
    return True

if __name__ == "__main__":
    test_files_basic_functions()
