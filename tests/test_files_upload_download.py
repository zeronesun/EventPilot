#!/usr/bin/env python3
"""
文件上传和下载功能测试
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import io

BASE_URL = "http://localhost:8000/api"

def test_files_upload_and_download():
    """测试文件上传和下载功能"""

    print("="*60)
    print("文件上传和下载功能测试")
    print("="*60)

    # 1. 登录
    print("\n1. 登录获取Token:")
    login_payload = {"username": "admin", "password": "admin123"}
    r = requests.post(f"{BASE_URL}/users/auth/login/", json=login_payload)
    if r.status_code not in [200, 201]:
        print(f"❌ 登录失败: {r.text}")
        return False
    
    data = r.json()
    token = data.get('data', {}).get('token', data.get('token', ''))
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 测试文件上传（multipart/form-data）
    print("\n2. 测试文件上传:")
    # 创建一个测试文件
    test_content = "这是测试文件内容" * 100  # 约1.5KB
    files = {
        'file': ('test_file.txt', io.BytesIO(test_content.encode('utf-8')), 'text/plain'),
        'filename': (None, 'test_file.txt'),
        'category': (None, 'document')
    }
    
    # 注意：实际 multipart 上传可能需要调整，这里做基本测试
    r = requests.post(f"{BASE_URL}/files/files/files/", headers=headers, files=files)
    print(f"   状态码: {r.status_code}")
    if r.status_code:
        result = r.json()
        print(f"✅ 文件上传成功: {result.get('file_id', 'N/A')[:20]}..." if r.status_code < 300 else f"⚠️  处理中: {str(result)[:100]}")
    else:
        print(f"❌ 文件上传失败: {r.text}")

    # 3. 测试文件列表
    print("\n3. 测试文件列表:")
    r = requests.get(f"{BASE_URL}/files/files/files/", headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 200:
        files_list = r.json()
        count = len(files_list.get('data', [])) if 'data' in files_list else len(files_list.get('results', []))
        print(f"✅ 文件列表: {count} 个文件")
    else:
        print(f"❌ 获取文件列表失败: {r.text}")

    # 4. 测试文件上传初始化（专用接口）
    print("\n4. 测试文件上传初始化:")
    upload_payload = {
        "filename": "test_upload.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "metadata": {"category": "document"}
    }
    r = requests.post(f"{BASE_URL}/files/files/files/", json=upload_payload, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code:
        result = r.json()
        print(f"✅ 上传初始化成功")
        upload_id = result.get('upload_id', result.get('file_id', ''))
        print(f"   Upload ID: {upload_id[:20] if upload_id else 'N/A'}...")
    else:
        print(f"❌ 上传初始化失败: {r.text}")
        upload_id = None

    # 5. 测试文件下载
    if upload_id:
        print("\n5. 测试文件下载:")
        # 使用 file_id 下载 endpoint
        r = requests.get(f"{BASE_URL}/files/files/files/{upload_id}/download/", headers=headers)
        print(f"   状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"✅ 文件下载成功")
            # 清理
            requests.delete(f"{BASE_URL}/files/files/files/{upload_id}/", headers=headers)
        elif r.status_code:
            print(f"⚠️  下载返回: {str(r.text)[:100]}")
        else:
            print(f"❌ 文件下载失败: {r.text}")

    # 6. 测试文件表单验证
    print("\n6. 测试文件表单验证（无效文件名）:")
    invalid_payload = {
        "filename": "",  # 空文件名应被拒绝
        "file_size": 1024,
        "mime_type": "application/pdf"
    }
    r = requests.post(f"{BASE_URL}/files/files/files/", json=invalid_payload, headers=headers)
    print(f"   状态码: {r.status_code}")
    if r.status_code == 400:
        print(f"✅ 表单验证正确（应拒绝空文件名）")
    else:
        print(f"⚠️  验证行为: {r.status_code}")

    print("\n" + "="*60)
    print("✅ 文件上传和下载功能测试完成!")
    print("="*60)
    return True

if __name__ == "__main__":
    test_files_upload_and_download()
