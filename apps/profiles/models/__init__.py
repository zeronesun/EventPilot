from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import json


class ContactProfile(models.Model):
    """
    关联方档案主表
    管理客户、供应商、合作伙伴的完整档案信息
    """
    
    class ProfileType(models.TextChoices):
        CLIENT = 'client', '客户'
        SUPPLIER = 'supplier', '供应商'
        PARTNER = 'partner', '合作伙伴'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', '活跃'
        INACTIVE = 'inactive', '非活跃'
        BLACKLISTED = 'blacklisted', '黑名单'
        PROSPECTIVE = 'prospective', '潜在'
        ARCHIVED = 'archived', '已归档'
    
    # 基础字段
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_type = models.CharField(
        max_length=20, 
        choices=ProfileType.choices,
        verbose_name="档案类型"
    )
    
    # 基本信息
    name = models.CharField(max_length=255, verbose_name="名称")
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="公司名称")
    legal_person = models.CharField(max_length=100, blank=True, verbose_name="法人代表")
    registration_number = models.CharField(max_length=50, blank=True, verbose_name="注册号")
    
    # 联系信息
    contact_info = models.JSONField(verbose_name="联系信息", default=dict)
    """
    contact_info 结构:
    {
        "address": {
            "street": "街道地址",
            "city": "城市",
            "province": "省份",
            "postal_code": "邮编",
            "country": "国家"
        },
        "phone": ["电话1", "电话2"],
        "email": ["邮箱1", "邮箱2"],
        "website": "网站地址",
        "social_media": {
            "wechat": "微信号",
            "linkedin": "LinkedIn",
            "weibo": "微博"
        }
    }
    """
    
    # 业务信息
    industry = models.CharField(max_length=100, blank=True, verbose_name="行业")
    business_scope = models.TextField(blank=True, verbose_name="业务范围")
    tags = models.JSONField(default=list, verbose_name="标签")
    """
    tags 示例: ["electronics", "software", "large-scale", "premium"]
    """
    
    # 状态管理
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default='prospective',
        verbose_name="状态"
    )
    
    # 评估和评级
    credit_score = models.IntegerField(default=0, verbose_name="信用评分", help_text="0-100分")
    quality_score = models.IntegerField(default=0, verbose_name="质量评分", help_text="0-100分")
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', '低风险'),
            ('medium', '中风险'),
            ('high', '高风险'),
        ],
        default='medium',
        verbose_name="风险等级"
    )
    
    # 系统字段
    is_deleted = models.BooleanField(default=False, verbose_name="已删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_profiles',
        verbose_name="删除人"
    )
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    last_contact_date = models.DateTimeField(null=True, blank=True, verbose_name="最后联系时间")
    
    # 所有者信息
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_profiles',
        verbose_name="档案所有者"
    )
    
    class Meta:
        db_table = 'contact_profiles'
        verbose_name = '关联方档案'
        verbose_name_plural = '关联方档案'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile_type']),
            models.Index(fields=['status']),
            models.Index(fields=['credit_score']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['created_at']),
            models.Index(fields=['deleted_at']),
        ]
    
    def __str__(self):
        return f"{self.get_profile_type_display()}: {self.name}"
    
    def update_contact_date(self):
        """更新最后联系时间"""
        self.last_contact_date = timezone.now()
        self.save(update_fields=['last_contact_date'])
    
    def get_primary_contact(self):
        """获取主要联系人"""
        return self.contacts.filter(is_primary=True).first()
    
    def calculate_aggregate_score(self):
        """计算综合评分"""
        # 基础计算：信用 + 质量
        if self.credit_score > 0 and self.quality_score > 0:
            return (self.credit_score + self.quality_score) // 2
        return max(self.credit_score, self.quality_score)
    
    def soft_delete(self, user):
        """软删除档案"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class ContactPerson(models.Model):
    """
    联系人详情表
    管理档案的主要联系人信息
    """
    
    class Position(models.TextChoices):
        CEO = 'ceo', 'CEO/总经理'
        DIRECTOR = 'director', '总监'
        MANAGER = 'manager', '经理'
        COORDINATOR = 'coordinator', '协调员'
        SALES = 'sales', '销售'
        TECHNICAL = 'technical', '技术'
        FINANCE = 'finance', '财务'
        OTHER = 'other', '其他'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        ContactProfile,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name="所属档案"
    )
    
    # 基本信息
    name = models.CharField(max_length=100, verbose_name="姓名")
    position = models.CharField(
        max_length=20,
        choices=Position.choices,
        blank=True,
        verbose_name="职位"
    )
    position_other = models.CharField(max_length=100, blank=True, verbose_name="其他职位")
    
    # 联系方式
    contact_info = models.JSONField(verbose_name="联系方式", default=dict)
    """
    contact_info 结构:
    {
        "phone": ["手机号1", "电话2"],
        "email": ["工作邮箱", "个人邮箱"],
        "wechat": "微信号",
        "linkedin": "LinkedIn",
        "qq": "QQ号"
    }
    """
    
    # 属性
    is_primary = models.BooleanField(default=False, verbose_name="主要联系人")
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    notes = models.TextField(blank=True, verbose_name="备注")
    
    # 系统字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contact_persons'
        verbose_name = '联系人'
        verbose_name_plural = '联系人'
        ordering = ['-is_primary', 'name']
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_position_display()}) - {self.profile.name}"


class InteractionHistory(models.Model):
    """
    交互历史记录表
    记录与关联方的所有交互和合作记录
    """
    
    class InteractionType(models.TextChoices):
        EVENT = 'event', '活动合作'
        CONTRACT = 'contract', '合同签署'
        COMMUNICATION = 'communication', '沟通联系'
        MEETING = 'meeting', '会议交流'
        PAYMENT = 'payment', '支付交易'
        SUPPORT = 'support', '技术支持'
        COMPLAINT = 'complaint', '投诉处理'
        NEGOTIATION = 'negotiation', '商务谈判'
        OTHER = 'other', '其他'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        ContactProfile,
        on_delete=models.CASCADE,
        related_name='interactions',
        verbose_name="关联档案"
    )
    
    # 交互基本信息
    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        verbose_name="交互类型"
    )
    title = models.CharField(max_length=255, verbose_name="交互标题")
    description = models.TextField(verbose_name="详细描述")
    
    # 关联信息
    related_event_id = models.UUIDField(null=True, blank=True, verbose_name="相关活动ID")
    related_project_id = models.CharField(max_length=100, blank=True, verbose_name="相关项目编号")
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name="元数据")
    """
    metadata 结构:
    {
        "value": 交易金额,
        "duration": 交互时长,
        "participants": 参与人员,
        "location": 地点,
        "outcome": 结果,
        "documents": 相关文档ID列表
    }
    """
    
    # 评估信息
    satisfaction_score = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="满意度评分",
        help_text="1-5分"
    )
    outcome_status = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="结果状态"
    )
    
    # 创建者信息
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_interactions',
        verbose_name="创建人"
    )
    
    # 时间戳
    interaction_date = models.DateTimeField(default=timezone.now, verbose_name="交互时间", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interaction_histories'
        verbose_name = '交互历史'
        verbose_name_plural = '交互历史'
        ordering = ['-interaction_date']
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['interaction_type']),
            models.Index(fields=['interaction_date']),
        ]
    
    def __str__(self):
        return f"{self.get_interaction_type_display()}: {self.title} - {self.profile.name}"
    
    def save(self, *args, **kwargs):
        # 保存后更新档案的最后联系时间
        super().save(*args, **kwargs)
        self.profile.update_contact_date()


class ProfileEvaluation(models.Model):
    """
    档案评估记录表
    记录对关联方的定性和定量评估
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        ContactProfile,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name="评估档案"
    )
    
    # 评估信息
    evaluation_date = models.DateTimeField(auto_now_add=True, verbose_name="评估时间")
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profile_evaluations',
        verbose_name="评估人"
    )
    
    # 评分
    credit_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="信用评分",
        help_text="0-100分"
    )
    quality_score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="质量评分",
        help_text="0-100分"
    )
    service_quality = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="服务质量",
        help_text="1-5分"
    )
    response_speed = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="响应速度",
        help_text="1-5分"
    )
    professional_ability = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="专业能力",
        help_text="1-5分"
    )
    
    # 评估内容
    evaluation_criteria = models.JSONField(default=dict, verbose_name="评估标准")
    """
    evaluation_criteria 结构:
    {
        "timeline": "按时交付",
        "quality": "质量控制",
        "communication": "沟通效率",
        "cost": "成本控制"
    }
    """
    
    # 风险评估
    risk_assessment = models.TextField(blank=True, verbose_name="风险评估")
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', '低风险'),
            ('medium', '中风险'),
            ('high', '高风险'),
        ],
        blank=True,
        verbose_name="风险等级"
    )
    
    # 建议和结论
    recommendations = models.TextField(verbose_name="建议和意见")
    overall_conclusion = models.CharField(max_length=500, blank=True, verbose_name="总体结论")
    
    # 下次评估
    next_evaluation_date = models.DateTimeField(null=True, blank=True, verbose_name="下次评估时间")
    
    class Meta:
        db_table = 'profile_evaluations'
        verbose_name = '档案评估'
        verbose_name_plural = '档案评估'
        ordering = ['-evaluation_date']
        indexes = [
            models.Index(fields=['profile']),
            models.Index(fields=['evaluation_date']),
            models.Index(fields=['evaluator']),
        ]
    
    def __str__(self):
        return f"评估: {self.profile.name} - {self.evaluation_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # 如果有评分，更新档案的评分
        super().save(*args, **kwargs)
        if self.credit_score is not None:
            self.profile.credit_score = self.credit_score
            self.profile.save(update_fields=['credit_score'])
        if self.quality_score is not None:
            # 将1-5分转换为0-100分
            converted_score = self.quality_score * 20
            self.profile.quality_score = converted_score
            self.profile.save(update_fields=['quality_score'])
        if self.risk_level:
            self.profile.risk_level = self.risk_level
            self.profile.save(update_fields=['risk_level'])