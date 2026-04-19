# WebSocket实时通讯基础设施测试脚本
# 用于验证Phase 2 WebSocket实现

import os
import sys
import django
import asyncio
import json
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 设置完成后导入模块
import django.db
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# 导入WebSocket模块
from apps.websocket.consumer import EventPilotConsumer, MessageType
from apps.websocket.connection_manager import ConnectionManager
from apps.websocket.notification_service import NotificationService, NotificationPriority
from apps.websocket.status_manager import StatusManager, UserStatus

# 配置Django用户模型
User = get_user_model()


class WebSocketTestRunner:
    """WebSocket测试运行器"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.notification_service = NotificationService()
        self.status_manager = StatusManager()
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始WebSocket基础设施测试...")
        print("=" * 60)
        
        tests = [
            ("连接管理器测试", self.test_connection_manager),
            ("通知服务测试", self.test_notification_service),
            ("状态管理器测试", self.test_status_manager),
            ("消息处理测试", self.test_message_processing),
            ("心跳检测测试", self.test_heartbeat),
            ("错误处理测试", self.test_error_handling),
        ]
        
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        self.print_summary()
    
    async def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 60)
        
        try:
            result = await test_func()
            if result:
                self.test_results.append((test_name, "✅ 通过", None))
                print(f"✅ 测试通过: {test_name}")
            else:
                self.test_results.append((test_name, "❌ 失败", "测试返回False"))
                print(f"❌ 测试失败: {test_name}")
        except Exception as e:
            self.test_results.append((test_name, "❌ 错误", str(e)))
            print(f"❌ 测试错误: {test_name}")
            print(f"   错误信息: {str(e)}")
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("📊 测试摘要")
        print("=" * 60)
        
        passed = sum(1 for _, status, _ in self.test_results if "通过" in status)
        failed = sum(1 for _, status, _ in self.test_results if "失败" in status or "错误" in status)
        total = len(self.test_results)
        
        for test_name, status, error in self.test_results:
            status_icon = "✅" if "通过" in status else "❌"
            print(f"{status_icon} {test_name}: {status}")
            if error:
                print(f"   错误: {error}")
        
        print("\n" + "-" * 60)
        print(f"总计: {total} | 通过: {passed} | 失败: {failed}")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 所有测试通过!")
        else:
            print("⚠️  存在失败的测试，请检查")
    
    async def test_connection_manager(self) -> bool:
        """测试连接管理器"""
        try:
            # 测试连接
            connection_id = "test_conn_1"
            user_id = 1
            device_id = "test_device"
            topics = {"user_1", "notifications"}
            
            connected = await self.connection_manager.connect(
                connection_id,
                user_id=user_id,
                device_id=device_id,
                topics=topics
            )
            
            if not connected:
                print("   ❌ 连接失败")
                return False
            
            # 检查连接信息
            conn_info = self.connection_manager.get_connection_info(connection_id)
            if conn_info is None:
                print("   ❌ 无法获取连接信息")
                return False
            
            if conn_info['user_id'] != user_id:
                print("   ❌ 用户ID不匹配")
                return False
            
            # 测试消息发送
            message = {'type': 'test', 'content': 'hello world'}
            sent = await self.connection_manager.send_message(connection_id, message)
            if not sent:
                print("   ❌ 消息发送失败")
                return False
            
            # 测试断开连接
            await self.connection_manager.disconnect(connection_id)
            
            # 检查统计
            stats = self.connection_manager.get_stats()
            if stats['total_connections'] < 1:
                print("   ❌ 连接统计不正确")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
            return False
    
    async def test_notification_service(self) -> bool:
        """测试通知服务"""
        try:
            # 测试创建通知
            notification = await self.notification_service.create_notification(
                user_id=1,
                title="测试通知",
                message="这是一条测试通知",
                notification_type=NotificationType.INFO,
                priority=NotificationPriority.NORMAL
            )
            
            if notification['user_id'] != 1:
                print("   ❌ 通知用户ID不正确")
                return False
            
            if notification['read']:
                print("   ❌ 通知不应已读")
                return False
            
            # 测试不同优先级
            await self.notification_service.create_notification(
                user_id=1,
                title="高优先级通知",
                message="高优先级",
                priority=NotificationPriority.HIGH
            )
            
            await self.notification_service.create_notification(
                user_id=1,
                title="紧急通知",
                message="紧急",
                priority=NotificationPriority.URGENT
            )
            
            # 检查队列统计
            stats = self.notification_service.get_queue_stats()
            if stats['total_queued'] < 3:
                print(f"   ❌ 队列统计不正确: {stats['total_queued']}")
                return False
            
            # 测试处理通知
            processed = await self.notification_service.process_notifications()
            if processed < 1:
                print("   ❌ 通知处理失败")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
            return False
    
    async def test_status_manager(self) -> bool:
        """测试状态管理器"""
        try:
            presence_service = self.status_manager.get_presence_service()
            
            # 测试更新用户状态
            updated = await presence_service.update_user_status(
                user_id=1,
                status=UserStatus.ONLINE,
                device_id="test_device"
            )
            
            if not updated:
                print("   ❌ 用户状态更新失败")
                return False
            
            # 检查用户状态
            user_status = presence_service.get_user_status(1)
            if user_status is None:
                print("   ❌ 无法获取用户状态")
                return False
            
            if user_status['status'] != 'online':
                print(f"   ❌ 状态不正确: {user_status['status']}")
                return False
            
            # 测试在线检查
            is_online = presence_service.is_user_online(1)
            if not is_online:
                print("   ❌ 用户应该在线")
                return False
            
            # 获取在线用户
            online_users = presence_service.get_online_users()
            if 1 not in online_users:
                print("   ❌ 用户ID 1应该在线用户列表中")
                return False
            
            # 测试断开处理
            await presence_service.user_disconnected(1, device_id="test_device")
            
            user_status = presence_service.get_user_status(1)
            if user_status and user_status['status'] != 'offline':
                print(f"   ❌ 用户应该离线: {user_status['status']}")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
            return False
    
    async def test_message_processing(self) -> bool:
        """测试消息处理"""
        try:
            # 测试消息路由
            connection_id = "test_conn_msg"
            
            await self.connection_manager.connect(
                connection_id,
                user_id=1,
                topics={"user_1"}
            )
            
            # 测试订阅
            topics = {"event_1", "task_1"}
            subscribed = await self.connection_manager.subscribe(connection_id, topics)
            if not subscribed:
                print("   ❌ 订阅失败")
                return False
            
            # 测试取消订阅
            unsubscribed = await self.connection_manager.unsubscribe(connection_id, {"event_1"})
            if not unsubscribed:
                print("   ❌ 取消订阅失败")
                return False
            
            await self.connection_manager.disconnect(connection_id)
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
            return False
    
    async def test_heartbeat(self) -> bool:
        """测试心跳检测"""
        try:
            connection_id = "test_conn_heartbeat"
            
            await self.connection_manager.connect(
                connection_id,
                user_id=1
            )
            
            # 更新心跳
            updated = await self.connection_manager.update_heartbeat(connection_id)
            if not updated:
                print("   ❌ 心跳更新失败")
                return False
            
            # 检查超时（应该没有超时）
            timeout_count = await self.connection_manager.check_timeouts()
            # 可能会返回0或其他数字，但不应该抛出异常
            
            await self.connection_manager.disconnect(connection_id)
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理"""
        try:
            # 测试发送到不存在的连接
            sent = await self.connection_manager.send_to_user(
                999,  # 不存在的用户
                {'type': 'test', 'message': 'hello'}
            )
            # 应该返回0（没有发送到任何连接）
            if sent != 0:
                print("   ⚠️  预期发送数为0")
                return False
            
            # 测试虚假通知标记
            marked = self.notification_service.mark_as_read(
                "fake_id",
                999
            )
            # 应该不抛出异常
            
            # 测试状态管理器的错误处理
            state = self.status_manager.get_event_state(999)
            if state is not None:
                print("   ⚠️  不存在的活动应返回None")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 测试异常: {str(e)}")
            return False


async def main():
    """主函数"""
    runner = WebSocketTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    print("🔧 WebSocket实时通讯基础设施验证")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行测试
    asyncio.run(main())
    
    print(f"⏱️  结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")