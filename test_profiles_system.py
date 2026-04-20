#!/usr/bin/env python3
"""
EventPilot Phase 3 - 关联方档案管理系统验证脚本
测试完整的档案管理功能
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.contrib.auth import get_user_model
from apps.profiles.models import ContactProfile, ContactPerson, InteractionHistory, ProfileEvaluation

User = get_user_model()


class ProfilesSystemTest:
    """关联方档案管理系统测试"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api"
        self.token = None
        self.test_user = None
        self.test_results = []
        self.profile_ids = []
        
    def log_test(self, test_name, result, details=""):
        """记录测试结果"""
        status = "✅ PASS" if result else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "result": result,
            "details": details,
            "status": status
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"     {details}")
    
    def test_backend_health(self):
        """测试后端健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            result = response.status_code == 200
            
            if result:
                data = response.json()
                self.log_test(
                    "后端健康检查",
                    True,
                    f"服务状态: {data['status']},档案管理: {data['features'].get('profile_management', 'unknown')}"
                )
            else:
                self.log_test("后端健康检查", False, f"状态码: {response.status_code}")
            
            return result
        except Exception as e:
            self.log_test("后端健康检查", False, f"错误: {str(e)}")
            return False
    
    def test_user_login(self):
        """测试用户登录并获取token"""
        # 确保测试用户存在
        self.test_user, created = User.objects.get_or_create(
            username='profile_test',
            defaults={
                'email': 'profile_test@example.com',
                'is_active': True
            }
        )
        if created:
            self.test_user.set_password('test123456')
            self.test_user.save()
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login/",
                json={
                    'username': 'profile_test',
                    'password': 'test123456'
                },
                timeout=10
            )
            result = response.status_code in [200, 201]
            
            if result:
                data = response.json()
                self.token = data.get('access') if isinstance(data, list) else data.get('data', {}).get('access')
                
                if not self.token:
                    self.token = data.get('access') if 'access' in data else None
                
                self.log_test(
                    "用户登录",
                    True if self.token else False,
                    f"用户: profile_test, Token状态: {'已获取' if self.token else '未获取'}"
                )
            else:
                self.log_test(
                    "用户登录",
                    False,
                    f"状态码: {response.status_code}, 响应: {response.text[:100]}"
                )
            
            return result and self.token is not None
        except Exception as e:
            self.log_test("用户登录", False, f"错误: {str(e)}")
            return False
    
    def test_profiles_api(self):
        """测试档案API功能"""
        if not self.token:
            self.log_test("档案API测试", False, "未获取到认证token")
            return False
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # 测试创建档案
        try:
            create_data = {
                "profile_type": "supplier",
                "name": "测试供应商科技有限公司",
                "company_name": "测试供应商科技有限公司",
                "industry": "软件开发",
                "status": "active",
                "credit_score": 75,
                "quality_score": 80,
                "risk_level": "low"
            }
            
            response = requests.post(
                f"{self.base_url}/profiles/",
                json=create_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                profile_data = response.json()
                profile_id = profile_data.get('id')
                self.profile_ids.append(profile_id)
                
                self.log_test(
                    "创建档案API",
                    True,
                    f"档案ID: {profile_id}, 名称: {create_data['name']}"
                )
                
                # 测试获取档案列表
                list_response = requests.get(
                    f"{self.base_url}/profiles/",
                    headers=headers,
                    timeout=10
                )
                
                if list_response.status_code == 200:
                    profiles = list_response.json() if isinstance(list_response.json(), list) else (list_response.json().get('results') or [])
                    self.log_test(
                        "获取档案列表API",
                        True,
                        f"返回档案数量: {len(profiles) if isinstance(profiles, list) else 'N/A'}"
                    )
                    
                    # 测试获取单个档案详情
                    if profile_id:
                        detail_response = requests.get(
                            f"{self.base_url}/profiles/{profile_id}/",
                            headers=headers,
                            timeout=10
                        )
                        
                        if detail_response.status_code == 200:
                            profile_detail = detail_response.json()
                            self.log_test(
                                "获取档案详情API",
                                True,
                                f"档案详情: {profile_detail.get('name', 'N/A')} (ID: {profile_id})"
                            )
                            
                            # 测试智能推荐功能
                            recommend_data = {
                                "event_type": "软件开发项目",
                                "min_credit_score": 50,
                                "max_risk_level": "medium",
                                "limit": 5
                            }
                            
                            rec_response = requests.post(
                                f"{self.base_url}/recommendations/suppliers/",
                                json=recommend_data,
                                headers=headers,
                                timeout=10
                            )
                            
                            if rec_response.status_code == 200:
                                rec_data = rec_response.json()
                                recommendations = rec_data.get('recommendations', [])
                                self.log_test(
                                    "智能推荐API",
                                    True,
                                    f"推荐供应商数量: {len(recommendations)}"
                                )
                                return True
                            else:
                                self.log_test(
                                    "智能推荐API",
                                    False,
                                    f"状态码: {rec_response.status_code}, 错误: {rec_response.text[:200]}"
                                )
                        else:
                            self.log_test(
                                "获取档案详情API",
                                False,
                                f"状态码: {detail_response.status_code}"
                            )
                    else:
                        self.log_test(
                            "获取档案详情API",
                            False,
                            "无效的profile_id"
                        )
                else:
                    self.log_test(
                    "获取档案列表API",
                    False,
                    f"状态码: {list_response.status_code}"
                )
            else:
                self.log_test(
                    "创建档案API",
                    False,
                    f"状态码: {response.status_code}, 错误: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("档案API测试", False, f"错误: {str(e)}")
            return False
        
        return True
    
    def test_data_models(self):
        """测试数据模型"""
        from django.db import connection
        
        try:
            # 检查数据库表
            with connection.cursor() as cursor:
                tables = [
                    'contact_profiles',
                    'contact_persons',
                    'interaction_histories', 
                    'profile_evaluations'
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.log_test(
                        f"数据库表: {table}",
                        True,
                        f"当前记录数: {count}"
                    )
                    
            return True
            
        except Exception as e:
            self.log_test("数据模型测试", False, f"错误: {str(e)}")
            return False
    
    def test_intelligent_recommender(self):
        """测试智能推荐引擎"""
        try:
            from apps.profiles.services import IntelligentRecommender
            
            # 测试推荐功能
            event_requirements = {
                "type": "软件开发项目",
                "min_credit_score": 60,
                "max_risk_level": "medium"
            }
            
            print("\n[智能推荐引擎] 测试规则推荐算法...")
            recommendations = IntelligentRecommender.recommend_suppliers(
                event_requirements=event_requirements,
                limit=5
            )
            
            print(f"[智能推荐引擎] 返回 {len(recommendations)} 个推荐结果")
            
            if len(recommendations) > 0:
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  推荐 {i}: {rec['name']} (分数: {rec['recommendation_score']})")
                    print(f"    理由: {', '.join(rec['reasons'])}")
                    
                self.log_test(
                    "智能推荐算法",
                    True,
                    f"成功生成 {len(recommendations)} 个推荐结果"
                )
                return True
            else:
                self.log_test(
                    "智能推荐算法",
                    True,
                    f"推荐引擎运行正常，当前暂无符合条件的档案"
                )
                return True
                
        except Exception as e:
            self.log_test("智能推荐算法", False, f"错误: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("EventPilot Phase 3 - 关联方档案管理系统验证")
        print("=" * 70)
        print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 系统健康检查
        print("=" * 70)
        print("第一部分: 基础设施测试")
        print("=" * 70)
        self.test_backend_health()
        
        # 数据模型测试
        print()
        self.test_data_models()
        
        # 功能测试
        print()
        print("=" * 70)
        print("第二部分: API功能测试")
        print("=" * 70)
        
        # 用户认证
        if self.test_user_login():
            # 档案API测试
            self.test_profiles_api()
            
            # 智能功能测试
            self.test_intelligent_recommender()
        
        # 测试结果汇总
        print()
        print("=" * 70)
        print("测试结果汇总")
        print("=" * 70)
        
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['result']])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print()
        for result in self.test_results:
            print(f"{result['status']} - {result['test']}")
            if result['details']:
                print(f"     {result['details']}")
        
        print()
        print(f"总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌") 
        print(f"成功率: {success_rate:.1f}%")
        print()
        
        if success_rate == 100:
            print("🎉 Phase 3 - 关联方档案管理系统验证全部通过！")
            print("📋 系统已准备好进入生产部署和用户测试阶段")
        elif success_rate >= 80:
            print("✅ Phase 3 基础功能已就绪，可进入Beta测试")
        else:
            print("⚠️  系统存在关键问题，需要修复")
        
        print()
        print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)


if __name__ == "__main__":
    try:
        test = ProfilesSystemTest()
        test.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试执行错误: {str(e)}")
        import traceback
        traceback.print_exc()