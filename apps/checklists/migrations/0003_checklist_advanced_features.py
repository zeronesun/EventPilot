# Generated migration for checklist advanced features

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0002_alter_checklistinstance_options_and_more'),
    ]

    operations = [
        # ChecklistVersion model
        migrations.CreateModel(
            name='ChecklistVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('version_number', models.CharField(max_length=50, verbose_name='版本号')),
                ('version_type', models.CharField(
                    choices=[('major', '重大更新'), ('minor', '次要更新'), ('patch', '补丁更新')],
                    default='patch', max_length=20, verbose_name='版本类型'
                )),
                ('changelog', models.TextField(verbose_name='变更日志')),
                ('changes', models.JSONField(default=dict, verbose_name='变更详情')),
                ('snapshot', models.JSONField(default=dict, verbose_name='数据快照')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否激活')),
                ('is_rollback', models.BooleanField(default=False, verbose_name='是否回滚版本')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('metadata', models.JSONField(default=dict, verbose_name='元数据')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL, 
                    to='users.user', verbose_name='创建人'
                )),
                ('instance', models.ForeignKey(
                    blank=True, null=True, on_delete=models.CASCADE,
                    related_name='versions', to='checklists.checklistinstance', verbose_name='实例'
                )),
                ('template', models.ForeignKey(
                    blank=True, null=True, on_delete=models.CASCADE,
                    related_name='versions', to='checklists.checklisttemplate', verbose_name='模板'
                )),
            ],
            options={
                'verbose_name': '清单版本',
                'verbose_name_plural': '清单版本',
                'db_table': 'checklist_versions',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['template'], name='idx_version_template'),
                    models.Index(fields=['instance'], name='idx_version_instance'),
                    models.Index(fields=['version_number'], name='idx_version_number'),
                    models.Index(fields=['is_active'], name='idx_version_active'),
                ],
            },
        ),

        # ChecklistVersionComparison model
        migrations.CreateModel(
            name='ChecklistVersionComparison',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('differences', models.JSONField(default=dict, verbose_name='差异')),
                ('summary', models.TextField(verbose_name='对比摘要')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    to='users.user', verbose_name='创建人'
                )),
                ('from_version', models.ForeignKey(
                    on_delete=models.CASCADE, related_name='comparisons_from',
                    to='checklists.checklistversion', verbose_name='源版本'
                )),
                ('to_version', models.ForeignKey(
                    on_delete=models.CASCADE, related_name='comparisons_to',
                    to='checklists.checklistversion', verbose_name='目标版本'
                )),
            ],
            options={
                'verbose_name': '清单版本对比',
                'verbose_name_plural': '清单版本对比',
                'db_table': 'checklist_version_comparisons',
                'ordering': ['-created_at'],
            },
        ),

        # ChecklistExport model
        migrations.CreateModel(
            name='ChecklistExport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('export_format', models.CharField(
                    choices=[('csv', 'CSV格式'), ('excel', 'Excel格式'), ('pdf', 'PDF格式'), ('json', 'JSON格式')],
                    max_length=20, verbose_name='导出格式'
                )),
                ('include_items', models.BooleanField(default=True, verbose_name='包含清单项')),
                ('include_attachments', models.BooleanField(default=False, verbose_name='包含附件')),
                ('include_metadata', models.BooleanField(default=False, verbose_name='包含元数据')),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待处理'), ('processing', '处理中'),
                        ('completed', '已完成'), ('failed', '失败')
                    ],
                    default='pending', max_length=20, verbose_name='状态'
                )),
                ('file_path', models.CharField(blank=True, max_length=500, verbose_name='文件路径')),
                ('file_url', models.URLField(blank=True, verbose_name='文件URL')),
                ('file_size', models.BigIntegerField(blank=True, null=True, verbose_name='文件大小')),
                ('error_message', models.TextField(blank=True, verbose_name='错误信息')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('metadata', models.JSONField(default=dict, verbose_name='元数据')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    to='users.user', verbose_name='创建人'
                )),
                ('instance', models.ForeignKey(
                    blank=True, null=True, on_delete=models.CASCADE,
                    related_name='exports', to='checklists.checklistinstance', verbose_name='实例'
                )),
                ('template', models.ForeignKey(
                    blank=True, null=True, on_delete=models.CASCADE,
                    related_name='exports', to='checklists.checklisttemplate', verbose_name='模板'
                )),
            ],
            options={
                'verbose_name': '清单导出',
                'verbose_name_plural': '清单导出',
                'db_table': 'checklist_exports',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['instance'], name='idx_export_instance'),
                    models.Index(fields=['template'], name='idx_export_template'),
                    models.Index(fields=['status'], name='idx_export_status'),
                    models.Index(fields=['export_format'], name='idx_export_format'),
                ],
            },
        ),

        # ChecklistImport model
        migrations.CreateModel(
            name='ChecklistImport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('import_format', models.CharField(max_length=20, verbose_name='导入格式')),
                ('file_path', models.CharField(max_length=500, verbose_name='文件路径')),
                ('file_size', models.BigIntegerField(blank=True, null=True, verbose_name='文件大小')),
                ('create_template', models.BooleanField(default=False, verbose_name='创建模板')),
                ('create_instance', models.BooleanField(default=False, verbose_name='创建实例')),
                ('update_existing', models.BooleanField(default=False, verbose_name='更新现有')),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待处理'), ('validating', '验证中'),
                        ('processing', '处理中'), ('completed', '已完成'), ('failed', '失败')
                    ],
                    default='pending', max_length=20, verbose_name='状态'
                )),
                ('total_records', models.IntegerField(default=0, verbose_name='总记录数')),
                ('processed_records', models.IntegerField(default=0, verbose_name='已处理记录数')),
                ('success_records', models.IntegerField(default=0, verbose_name='成功记录数')),
                ('failed_records', models.IntegerField(default=0, verbose_name='失败记录数')),
                ('error_message', models.TextField(blank=True, verbose_name='错误信息')),
                ('validation_errors', models.JSONField(default=list, verbose_name='验证错误')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('metadata', models.JSONField(default=dict, verbose_name='元数据')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    to='users.user', verbose_name='创建人'
                )),
            ],
            options={
                'verbose_name': '清单导入',
                'verbose_name_plural': '清单导入',
                'db_table': 'checklist_imports',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['status'], name='idx_import_status'),
                    models.Index(fields=['import_format'], name='idx_import_format'),
                ],
            },
        ),

        # ChecklistVerification model
        migrations.CreateModel(
            name='ChecklistVerification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('planned_start_time', models.DateTimeField(verbose_name='计划开始时间')),
                ('planned_end_time', models.DateTimeField(verbose_name='计划结束时间')),
                ('actual_start_time', models.DateTimeField(blank=True, null=True, verbose_name='实际开始时间')),
                ('actual_end_time', models.DateTimeField(blank=True, null=True, verbose_name='实际结束时间')),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待核验'), ('in_progress', '核验中'), ('on_hold', '暂停'),
                        ('completed', '已完成'), ('failed', '失败'), ('cancelled', '已取消')
                    ],
                    default='pending', max_length=20, verbose_name='核验状态'
                )),
                ('approval_status', models.CharField(
                    choices=[
                        ('not_required', '无需审批'), ('pending', '待审批'),
                        ('approved', '已批准'), ('rejected', '已拒绝')
                    ],
                    default='not_required', max_length=20, verbose_name='审批状态'
                )),
                ('total_items', models.IntegerField(default=0, verbose_name='总项数')),
                ('verified_items', models.IntegerField(default=0, verbose_name='已核验项数')),
                ('passed_items', models.IntegerField(default=0, verbose_name='通过项数')),
                ('failed_items', models.IntegerField(default=0, verbose_name='失败项数')),
                ('requires_approval', models.BooleanField(default=False, verbose_name='需要审批')),
                ('approved_at', models.DateTimeField(blank=True, null=True, verbose_name='审批时间')),
                ('rejection_reason', models.TextField(blank=True, verbose_name='拒绝原因')),
                ('has_exceptions', models.BooleanField(default=False, verbose_name='有异常')),
                ('exception_details', models.JSONField(default=list, verbose_name='异常详情')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('metadata', models.JSONField(default=dict, verbose_name='元数据')),
                ('instance', models.ForeignKey(
                    on_delete=models.CASCADE, related_name='verifications',
                    to='checklists.checklistinstance', verbose_name='清单实例'
                )),
                ('approved_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    related_name='approvals', to='users.user', verbose_name='审批人'
                )),
                ('verified_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    related_name='verifications', to='users.user', verbose_name='核验人'
                )),
            ],
            options={
                'verbose_name': '清单核验',
                'verbose_name_plural': '清单核验',
                'db_table': 'checklist_verifications',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['instance'], name='idx_verification_instance'),
                    models.Index(fields=['status'], name='idx_verification_status'),
                    models.Index(fields=['approval_status'], name='idx_verification_approval'),
                    models.Index(fields=['verified_by'], name='idx_verification_verifier'),
                    models.Index(fields=['requires_approval'], name='idx_verification_requires_approval'),
                ],
            },
        ),

        # ChecklistVerificationDetail model
        migrations.CreateModel(
            name='ChecklistVerificationDetail',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('status', models.CharField(max_length=20, verbose_name='状态')),
                ('result', models.CharField(max_length=20, verbose_name='结果')),
                ('evidence', models.TextField(blank=True, verbose_name='证据描述')),
                ('attachments', models.JSONField(default=list, verbose_name='附件')),
                ('verified_at', models.DateTimeField(verbose_name='核验时间')),
                ('location', models.JSONField(blank=True, null=True, verbose_name='位置(GPS)')),
                ('notes', models.TextField(blank=True, verbose_name='备注')),
                ('metadata', models.JSONField(default=dict, verbose_name='元数据')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('checklist_item', models.ForeignKey(
                    on_delete=models.CASCADE, to='checklists.checklistitem', verbose_name='清单项'
                )),
                ('verification', models.ForeignKey(
                    on_delete=models.CASCADE, related_name='details',
                    to='checklists.checklistverification', verbose_name='核验记录'
                )),
                ('verified_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    to='users.user', verbose_name='核验人'
                )),
            ],
            options={
                'verbose_name': '清单核验详情',
                'verbose_name_plural': '清单核验详情',
                'db_table': 'checklist_verification_details',
                'ordering': ['verified_at'],
                'indexes': [
                    models.Index(fields=['verification'], name='idx_verification_detail_verification'),
                    models.Index(fields=['checklist_item'], name='idx_verification_detail_item'),
                    models.Index(fields=['status'], name='idx_verification_detail_status'),
                ],
            },
        ),

        # ChecklistVerificationException model
        migrations.CreateModel(
            name='ChecklistVerificationException',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('exception_type', models.CharField(
                    choices=[
                        ('missing_item', '缺失项'), ('failed_validation', '验证失败'),
                        ('timeout', '超时'), ('access_denied', '访问拒绝'),
                        ('system_error', '系统错误'), ('other', '其他')
                    ],
                    max_length=30, verbose_name='异常类型'
                )),
                ('status', models.CharField(
                    choices=[
                        ('open', '待处理'), ('in_progress', '处理中'),
                        ('resolved', '已解决'), ('ignored', '已忽略')
                    ],
                    default='open', max_length=20, verbose_name='状态'
                )),
                ('title', models.CharField(max_length=255, verbose_name='异常标题')),
                ('description', models.TextField(verbose_name='异常描述')),
                ('severity', models.CharField(max_length=20, verbose_name='严重程度')),
                ('resolution', models.TextField(blank=True, verbose_name='解决方案')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='解决时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('metadata', models.JSONField(default=dict, verbose_name='元数据')),
                ('verification', models.ForeignKey(
                    on_delete=models.CASCADE, related_name='exceptions',
                    to='checklists.checklistverification', verbose_name='核验记录'
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    related_name='assigned_exceptions', to='users.user', verbose_name='处理人'
                )),
                ('checklist_item', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    to='checklists.checklistitem', verbose_name='相关清单项'
                )),
                ('resolved_by', models.ForeignKey(
                    blank=True, null=True, on_delete=models.SET_NULL,
                    related_name='resolved_exceptions', to='users.user', verbose_name='解决人'
                )),
            ],
            options={
                'verbose_name': '清单核验异常',
                'verbose_name_plural': '清单核验异常',
                'db_table': 'checklist_verification_exceptions',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['verification'], name='idx_verification_exception_verification'),
                    models.Index(fields=['status'], name='idx_verification_exception_status'),
                    models.Index(fields=['exception_type'], name='idx_verification_exception_type'),
                    models.Index(fields=['assigned_to'], name='idx_verification_exception_assigned'),
                ],
            },
        ),
    ]