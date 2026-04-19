import logging
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.users.models import User, UserRole
from apps.users.services.user_service import UserService

logger = logging.getLogger(__name__)


class UserImportService:
    """用户批量导入服务"""
    
    # 导入状态映射
    IMPORT_STATUS = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败',
        'partial': '部分成功'
    }
    
    # 字段映射 - CSV/Excel列标题到数据库字段
    FIELD_MAPPING = {
        '用户名': 'username',
        'username': 'username',
        '邮箱': 'email',
        'email': 'email',
        '密码': 'password',
        'password': 'password',
        '名': 'first_name',
        'first_name': 'first_name',
        '姓': 'last_name',
        'last_name': 'last_name',
        '手机号': 'phone',
        'phone': 'phone',
        '部门': 'department',
        'department': 'department',
        '职位': 'position',
        'position': 'position',
        '角色': 'role',
        'role': 'role',
        '头像URL': 'avatar_url',
        'avatar_url': 'avatar_url'
    }
    
    # 默认密码设置
    DEFAULT_PASSWORD = 'TempPassword123!'
    
    # 角色映射
    ROLE_MAPPING = {
        '系统管理员': 'admin',
        'admin': 'admin',
        '项目负责人': 'project_owner',
        'project_owner': 'project_owner',
        '执行成员': 'executor',
        'executor': 'executor',
        '只读观察者': 'observer',
        'observer': 'observer'
    }
    
    @staticmethod
    def normalize_role(role: Any) -> str:
        """规范化角色值"""
        if not role:
            return 'executor'  # 默认角色
        
        role_str = str(role).strip().lower()
        
        # 直接匹配
        for key, value in UserImportService.ROLE_MAPPING.items():
            if key.lower() == role_str:
                return value
        
        # 模糊匹配
        if 'admin' in role_str:
            return 'admin'
        elif 'owner' in role_str or 'lead' in role_str:
            return 'project_owner'
        elif 'exec' in role_str or 'member' in role_str or '用户' in role_str:
            return 'executor'
        elif 'read' in role_str or 'obs' in role_str:
            return 'observer'
        
        return 'executor'  # 默认角色
    
    @staticmethod
    def normalize_field_names(record: Dict) -> Dict:
        """规范化字段名称"""
        normalized = {}
        
        for key, value in record.items():
            normalized_key = UserImportService.FIELD_MAPPING.get(key.strip(), key.strip().lower())
            
            # 角色特殊处理
            if normalized_key == 'role':
                normalized[normalized_key] = UserImportService.normalize_role(value)
            else:
                normalized[normalized_key] = value
        
        return normalized
    
    @staticmethod
    def validate_import_record(record: Dict, index: int) -> Tuple[bool, List[str]]:
        """验证单条导入记录"""
        errors = []
        
        # 必填字段检查
        if not record.get('username') or not str(record['username']).strip():
            errors.append(f'行 {index}: 用户名不能为空')
        
        if not record.get('email') or not '@' in str(record['email']):
            errors.append(f'行 {index}: 邮箱格式不正确')
        
        # 字段长度检查
        username = str(record.get('username', '')).strip()
        if len(username) < 3:
            errors.append(f'行 {index}: 用户名长度至少3位')
        
        if len(username) > 50:
            errors.append(f'行 {index}: 用户名长度不能超过50位')
        
        # 角色验证
        role = UserImportService.normalize_role(record.get('role'))
        valid_roles = ['admin', 'project_owner', 'executor', 'observer']
        if role not in valid_roles:
            errors.append(f'行 {index}: 无效的角色值')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def prepare_password(record: Dict) -> str:
        """准备用户密码"""
        password = record.get('password')
        
        if password and str(password).strip():
            return str(password).strip()
        
        # 如果没有提供密码，生成临时密码
        username = record.get('username', '')
        return f"{username}123!"[:8] if username else UserImportService.DEFAULT_PASSWORD
    
    @staticmethod
    def import_users_from_list(users_data: List[Dict], send_welcome_email: bool = False, 
                               force_password_change: bool = True) -> Dict[str, Any]:
        """从列表批量导入用户
        
        Args:
            users_data: 用户数据列表
            send_welcome_email: 是否发送欢迎邮件
            force_password_change: 是否强制用户修改密码
        
        Returns:
            导入结果字典
        """
        results = {
            'success': True,
            'total': len(users_data),
            'imported': 0,
            'failed': 0,
            'errors': [],
            'user_ids': [],
            'status': 'completed'
        }
        
        try:
            with transaction.atomic():
                for index, user_data in enumerate(users_data, 1):
                    # 规范化字段名
                    normalized_data = UserImportService.normalize_field_names(user_data)
                    
                    # 验证记录
                    is_valid, validation_errors = UserImportService.validate_import_record(
                        normalized_data, index
                    )
                    
                    if not is_valid:
                        results['failed'] += 1
                        results['errors'].extend(validation_errors)
                        continue
                    
                    # 准备密码
                    normalized_data['password'] = UserImportService.prepare_password(normalized_data)
                    
                    # 检查用户是否已存在
                    username = normalized_data['username']
                    email = normalized_data['email']
                    
                    if User.objects.filter(username=username).exists():
                        results['failed'] += 1
                        results['errors'].append(f'行 {index}: 用户名 {username} 已存在')
                        continue
                    
                    if User.objects.filter(email=email).exists():
                        results['failed'] += 1
                        results['errors'].append(f'行 {index}: 邮箱 {email} 已存在')
                        continue
                    
                    # 创建用户
                    try:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=normalized_data['password'],
                            first_name=normalized_data.get('first_name', ''),
                            last_name=normalized_data.get('last_name', ''),
                            phone=normalized_data.get('phone', ''),
                            department=normalized_data.get('department', ''),
                            position=normalized_data.get('position', ''),
                            avatar_url=normalized_data.get('avatar_url', ''),
                        )
                        
                        # 设置密码相关字段
                        user.password_changed_at = timezone.now()
                        user.force_password_change = force_password_change
                        user.save()
                        
                        # 分配角色
                        role = UserImportService.normalize_role(normalized_data.get('role'))
                        UserRole.objects.create(user=user, role=role)
                        
                        # 记录导入活动
                        UserService.log_user_activity(
                            user=user,
                            activity_type='bulk_operation',
                            details={
                                'action': 'user_import',
                                'import_method': 'listImport'
                            }
                        )
                        
                        results['imported'] += 1
                        results['user_ids'].append(str(user.id))
                        
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f'行 {index}: 创建用户失败 - {str(e)}')
                        logger.error(f"用户导入失败 (行 {index}): {e}")
                
                # 设置最终状态
                if results['failed'] > 0 and results['imported'] > 0:
                    results['status'] = 'partial'
                elif results['failed'] > 0 and results['imported'] == 0:
                    results['status'] = 'failed'
                    results['success'] = False
                
                # 如果没有成功导入任何用户，回滚事务
                if results['imported'] == 0:
                    transaction.rollback()
                    return results
                
                logger.info(f"用户导入完成: 成功 {results['imported']}, 失败 {results['failed']}")
                
        except Exception as e:
            logger.error(f"用户导入过程中发生错误: {e}")
            transaction.rollback()
            results['success'] = False
            results['status'] = 'failed'
            results['errors'].append(f'导入过程中发生严重错误: {str(e)}')
        
        return results
    
    @staticmethod
    def validate_import_template(data: List[Dict]) -> Tuple[bool, List[str]]:
        """验证导入数据模板"""
        errors = []
        
        if not data or len(data) == 0:
            errors.append('导入数据为空')
            return False, errors
        
        # 检查必需字段是否存在
        first_record = data[0]
        normalized = UserImportService.normalize_field_names(first_record)
        
        required_fields = ['username', 'email']
        missing_fields = []
        
        for field in required_fields:
            if field not in normalized or not normalized[field]:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append(f'缺少必需字段: {", ".join(missing_fields)}')
        
        # 检查数据格式
        if len(data) > 1000:
            errors.append('单次导入数据量不能超过1000条')
        
        return len(errors) == 0, errors
    
    @staticmethod
    def generate_import_summary(results: Dict[str, Any]) -> str:
        """生成导入摘要"""
        summary_lines = [
            f"用户导入完成 状态: {results['status']}",
            f"总记录数: {results['total']}",
            f"成功导入: {results['imported']}",
            f"失败记录: {results['failed']}",
        ]
        
        if results['errors']:
            summary_lines.append("\n错误详情:")
            for error in results['errors'][:10]:  # 只显示前10个错误
                summary_lines.append(f"  - {error}")
            if len(results['errors']) > 10:
                summary_lines.append(f"  ... 还有 {len(results['errors']) - 10} 个错误")
        
        if results['imported'] > 0 and results.get('force_password_change'):
            summary_lines.append("\n提示: 已为所有用户设置强制修改密码")
        
        return "\n".join(summary_lines)