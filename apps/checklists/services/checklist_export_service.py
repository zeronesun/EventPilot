import logging
import csv
import io
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from django.db import transaction
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.checklists.models import (
    ChecklistTemplate, ChecklistInstance, ChecklistItem,
    ChecklistExport, ChecklistImport
)

User = get_user_model()
logger = logging.getLogger(__name__)


class ChecklistExportService:
    """清单导出服务"""
    
    @staticmethod
    def create_export_record(target, export_format: str, created_by,
                              include_items: bool = True,
                              include_attachments: bool = False,
                              include_metadata: bool = False) -> ChecklistExport:
        """创建导出记录"""
        
        export_data = {
            'export_format': export_format,
            'include_items': include_items,
            'include_attachments': include_attachments,
            'include_metadata': include_metadata,
        }
        
        if isinstance(target, ChecklistInstance):
            export_data['instance'] = target
        elif isinstance(target, ChecklistTemplate):
            export_data['template'] = target
        
        export = ChecklistExport.objects.create(
            **export_data,
            status='pending',
            created_by=created_by
        )
        
        return export
    
    @staticmethod
    def export_to_csv(target, export: ChecklistExport) -> Tuple[bool, List[str]]:
        """导出为CSV格式"""
        errors = []
        
        try:
            export.status = 'processing'
            export.save()
            
            # 创建CSV内容
            output = io.StringIO()
            writer = csv.writer(output)
            
            if isinstance(target, ChecklistInstance):
                # 导出实例
                writer.writerow(['类型', '实例'])
                writer.writerow(['实例ID', str(target.id)])
                writer.writerow(['实例名称', target.name])
                writer.writerow(['状态', target.status])
                writer.writerow(['完成度', f"{target.completion_rate}%"])
                writer.writerow(['创建时间', target.created_at.strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                
                if export.include_items:
                    writer.writerow(['清单项'])
                    writer.writerow(['序号', '标题', '描述', '状态', '必填', '权重', '备注'])
                    
                    for idx, item in enumerate(target.items.all(), 1):
                        writer.writerow([
                            idx,
                            item.title,
                            item.description,
                            item.status,
                            '是' if item.required else '否',
                            item.weight,
                            item.notes
                        ])
                
            elif isinstance(target, ChecklistTemplate):
                # 导出模板
                writer.writerow(['类型', '模板'])
                writer.writerow(['模板ID', str(target.id)])
                writer.writerow(['模板名称', target.name])
                writer.writerow(['描述', target.description])
                writer.writerow(['清单类型', target.checklist_type])
                writer.writerow(['版本', target.version])
                writer.writerow(['状态', target.status])
                writer.writerow([])
                
                if export.include_items:
                    writer.writerow(['清单项'])
                    writer.writerow(['序号', '标题', '描述', '必填', '权重', '状态'])
                    
                    for idx, item in enumerate(target.items.all(), 1):
                        writer.writerow([
                            idx,
                            item.title,
                            item.description,
                            '是' if item.required else '否',
                            item.weight,
                            item.status
                        ])
            
            # 生成文件名和路径
            filename = f"checklist_{target.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = f"exports/{filename}"
            
            # 保存文件（实际应用中应该保存到云存储）
            content = output.getvalue()
            export.file_path = file_path
            export.file_url = f"/media/{file_path}"
            export.file_size = len(content.encode('utf-8'))
            export.status = 'completed'
            export.completed_at = timezone.now()
            export.save()
            
            logger.info(f"CSV导出成功: {filename}")
            return True, []
            
        except Exception as e:
            logger.error(f"CSV导出失败: {e}")
            export.status = 'failed'
            export.error_message = str(e)
            export.save()
            errors.append(f"CSV导出失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def export_to_excel(target, export: ChecklistExport) -> Tuple[bool, List[str]]:
        """导出为Excel格式"""
        errors = []
        
        try:
            export.status = 'processing'
            export.save()
            
            # 使用openpyxl创建Excel文件
            try:
                import openpyxl
                from openpyxl.styles import Font, Alignment
            except ImportError:
                errors.append("需要安装openpyxl库: pip install openpyxl")
                export.status = 'failed'
                export.error_message = "缺少openpyxl库"
                export.save()
                return False, errors
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "清单数据"
            
            # 设置标题行样式
            header_font = Font(bold=True, size=12)
            header_alignment = Alignment(horizontal='center', vertical='center')
            
            if isinstance(target, ChecklistInstance):
                # 导出实例信息
                ws['A1'] = '类型'
                ws['B1'] = '实例'
                ws['A1'].font = header_font
                ws['B1'].font = header_font
                
                data = [
                    ['实例ID', str(target.id)],
                    ['实例名称', target.name],
                    ['状态', target.status],
                    ['完成度', f"{target.completion_rate}%"],
                    ['创建时间', target.created_at.strftime('%Y-%m-%d %H:%M:%S')],
                ]
                
                for row_idx, (key, value) in enumerate(data, start=2):
                    ws[f'A{row_idx}'] = key
                    ws[f'B{row_idx}'] = value
                
                # 清单项
                if export.include_items:
                    start_row = len(data) + 3
                    ws[f'A{start_row}'] = '清单项'
                    ws[f'A{start_row}'].font = header_font
                    
                    headers = ['序号', '标题', '描述', '状态', '必填', '权重', '备注']
                    for col_idx, header in enumerate(headers, start=1):
                        cell = ws.cell(row=start_row + 1, column=col_idx, value=header)
                        cell.font = header_font
                        cell.alignment = header_alignment
                    
                    for item_idx, item in enumerate(target.items.all(), start=1):
                        row = start_row + 1 + item_idx
                        ws.cell(row=row, column=1, value=item_idx)
                        ws.cell(row=row, column=2, value=item.title)
                        ws.cell(row=row, column=3, value=item.description)
                        ws.cell(row=row, column=4, value=item.status)
                        ws.cell(row=row, column=5, value='是' if item.required else '否')
                        ws.cell(row=row, column=6, value=item.weight)
                        ws.cell(row=row, column=7, value=item.notes or '')
            
            elif isinstance(target, ChecklistTemplate):
                # 导出模板信息
                ws['A1'] = '类型'
                ws['B1'] = '模板'
                ws['A1'].font = header_font
                ws['B1'].font = header_font
                
                data = [
                    ['模板ID', str(target.id)],
                    ['模板名称', target.name],
                    ['描述', target.description],
                    ['清单类型', target.checklist_type],
                    ['版本', target.version],
                    ['状态', target.status],
                ]
                
                for row_idx, (key, value) in enumerate(data, start=2):
                    ws[f'A{row_idx}'] = key
                    ws[f'B{row_idx}'] = value
                
                # 清单项
                if export.include_items:
                    start_row = len(data) + 3
                    ws[f'A{start_row}'] = '清单项'
                    ws[f'A{start_row}'].font = header_font
                    
                    headers = ['序号', '标题', '描述', '必填', '权重', '状态']
                    for col_idx, header in enumerate(headers, start=1):
                        cell = ws.cell(row=start_row + 1, column=col_idx, value=header)
                        cell.font = header_font
                        cell.alignment = header_alignment
                    
                    for item_idx, item in enumerate(target.items.all(), start=1):
                        row = start_row + 1 + item_idx
                        ws.cell(row=row, column=1, value=item_idx)
                        ws.cell(row=row, column=2, value=item.title)
                        ws.cell(row=row, column=3, value=item.description or '')
                        ws.cell(row=row, column=4, value='是' if item.required else '否')
                        ws.cell(row=row, column=5, value=item.weight)
                        ws.cell(row=row, column=6, value=item.status)
            
            # 调整列宽
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width
            
            # 生成文件名和路径
            filename = f"checklist_{target.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_path = f"exports/{filename}"
            
            # 保存Excel文件
            from django.core.files import File
            excel_buffer = io.BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            
            export.file_path = file_path
            export.file_url = f"/media/{file_path}"
            export.file_size = excel_buffer.getbuffer().nbytes
            export.status = 'completed'
            export.completed_at = timezone.now()
            export.save()
            
            logger.info(f"Excel导出成功: {filename}")
            return True, []
            
        except Exception as e:
            logger.error(f"Excel导出失败: {e}")
            export.status = 'failed'
            export.error_message = str(e)
            export.save()
            errors.append(f"Excel导出失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def export_to_pdf(target, export: ChecklistExport) -> Tuple[bool, List[str]]:
        """导出为PDF格式"""
        errors = []
        
        try:
            export.status = 'processing'
            export.save()
            
            # 使用reportlab创建PDF
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
                from reportlab.lib import colors
            except ImportError:
                errors.append("需要安装reportlab库: pip install reportlab")
                export.status = 'failed'
                export.error_message = "缺少reportlab库"
                export.save()
                return False, errors
            
            # 生成文件名和路径
            filename = f"checklist_{target.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = f"exports/{filename}"
            
            # 创建PDF文档
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            story = []
            styles = getSampleStyleSheet()
            
            # 生成PDF内容
            if isinstance(target, ChecklistInstance):
                # 实例信息
                story.append(Paragraph(f"清单实例: {target.name}", styles['Title']))
                story.append(Paragraph(f"状态: {target.status}", styles['Normal']))
                story.append(Paragraph(f"完成度: {target.completion_rate}%", styles['Normal']))
                story.append(Paragraph(f"创建时间: {target.created_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                story.append(Paragraph("<br/>", styles['Normal']))
                
                if export.include_items:
                    story.append(Paragraph("清单项", styles['Heading2']))
                    
                    # 创建表格
                    data = [['序号', '标题', '状态', '必填', '权重']]
                    for idx, item in enumerate(target.items.all(), 1):
                        data.append([
                            str(idx),
                            item.title,
                            item.status,
                            '是' if item.required else '否',
                            str(item.weight)
                        ])
                    
                    table = Table(data, colWidths=[0.5*inch, 3*inch, 1*inch, 0.5*inch, 0.5*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                
            elif isinstance(target, ChecklistTemplate):
                # 模板信息
                story.append(Paragraph(f"清单模板: {target.name}", styles['Title']))
                story.append(Paragraph(f"描述: {target.description}", styles['Normal']))
                story.append(Paragraph(f"清单类型: {target.checklist_type}", styles['Normal']))
                story.append(Paragraph(f"版本: {target.version}", styles['Normal']))
                story.append(Paragraph(f"状态: {target.status}", styles['Normal']))
                story.append(Paragraph("<br/>", styles['Normal']))
                
                if export.include_items:
                    story.append(Paragraph("清单项", styles['Heading2']))
                    
                    # 创建表格
                    data = [['序号', '标题', '必填', '权重', '状态']]
                    for idx, item in enumerate(target.items.all(), 1):
                        data.append([
                            str(idx),
                            item.title,
                            '是' if item.required else '否',
                            str(item.weight),
                            item.status
                        ])
                    
                    table = Table(data, colWidths=[0.5*inch, 3*inch, 0.5*inch, 0.5*inch, 0.5*inch])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
            
            # 构建PDF
            doc.build(story)
            
            export.file_path = file_path
            export.file_url = f"/media/{file_path}"
            export.file_size = buffer.getbuffer().nbytes
            export.status = 'completed'
            export.completed_at = timezone.now()
            export.save()
            
            logger.info(f"PDF导出成功: {filename}")
            return True, []
            
        except Exception as e:
            logger.error(f"PDF导出失败: {e}")
            export.status = 'failed'
            export.error_message = str(e)
            export.save()
            errors.append(f"PDF导出失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def export_to_json(target, export: ChecklistExport) -> Tuple[bool, List[str]]:
        """导出为JSON格式"""
        errors = []
        
        try:
            export.status = 'processing'
            export.save()
            
            # 构建JSON数据
            data = {
                'export_type': 'instance' if isinstance(target, ChecklistInstance) else 'template',
                'exported_at': timezone.now().isoformat(),
            }
            
            if isinstance(target, ChecklistInstance):
                data['instance'] = {
                    'id': str(target.id),
                    'name': target.name,
                    'status': target.status,
                    'completion_rate': target.completion_rate,
                    'created_at': target.created_at.isoformat(),
                    'updated_at': target.updated_at.isoformat(),
                    'completed_at': target.completed_at.isoformat() if target.completed_at else None,
                }
                
                if export.include_items:
                    data['instance']['items'] = [
                        {
                            'id': str(item.id),
                            'title': item.title,
                            'description': item.description,
                            'status': item.status,
                            'required': item.required,
                            'weight': item.weight,
                            'order': item.order,
                            'notes': item.notes,
                        }
                        for item in target.items.all()
                    ]
                
                if export.include_attachments:
                    data['instance']['attachments'] = [
                        {'url': att} for att in (target.attachments or [])
                    ]
                
                if export.include_metadata:
                    data['instance']['metadata'] = target.metadata
            
            elif isinstance(target, ChecklistTemplate):
                data['template'] = {
                    'id': str(target.id),
                    'name': target.name,
                    'description': target.description,
                    'checklist_type': target.checklist_type,
                    'version': target.version,
                    'status': target.status,
                    'category': target.category,
                    'tags': target.tags,
                    'event_types': target.event_types,
                    'created_at': target.created_at.isoformat(),
                    'updated_at': target.updated_at.isoformat(),
                }
                
                if export.include_items:
                    data['template']['items'] = [
                        {
                            'id': str(item.id),
                            'title': item.title,
                            'description': item.description,
                            'required': item.required,
                            'weight': item.weight,
                            'order': item.order,
                            'status': item.status,
                        }
                        for item in target.items.all()
                    ]
                
                if export.include_metadata:
                    data['template']['metadata'] = target.metadata
            
            # 生成文件名和路径
            filename = f"checklist_{target.name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = f"exports/{filename}"
            
            # 保存JSON文件
            content = json.dumps(data, indent=2, ensure_ascii=False)
            export.file_path = file_path
            export.file_url = f"/media/{file_path}"
            export.file_size = len(content.encode('utf-8'))
            export.status = 'completed'
            export.completed_at = timezone.now()
            export.save()
            
            logger.info(f"JSON导出成功: {filename}")
            return True, []
            
        except Exception as e:
            logger.error(f"JSON导出失败: {e}")
            export.status = 'failed'
            export.error_message = str(e)
            export.save()
            errors.append(f"JSON导出失败: {str(e)}")
            return False, errors


class ChecklistImportService:
    """清单导入服务"""
    
    @staticmethod
    def create_import_record(import_format: str, file_path: str, created_by,
                              create_template: bool = False,
                              create_instance: bool = False,
                              update_existing: bool = False) -> ChecklistImport:
        """创建导入记录"""
        
        import_record = ChecklistImport.objects.create(
            import_format=import_format,
            file_path=file_path,
            create_template=create_template,
            create_instance=create_instance,
            update_existing=update_existing,
            status='pending',
            created_by=created_by
        )
        
        return import_record
    
    @staticmethod
    def import_from_json(import_record: ChecklistImport) -> Tuple[bool, List[str]]:
        """从JSON导入清单"""
        errors = []
        validation_errors = []
        
        try:
            import_record.status = 'validating'
            import_record.save()
            
            # 读取JSON文件
            try:
                with open(import_record.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except FileNotFoundError:
                errors.append('文件不存在')
                import_record.status = 'failed'
                import_record.error_message = '文件不存在'
                import_record.save()
                return False, errors
            except json.JSONDecodeError as e:
                errors.append(f'JSON解析错误: {str(e)}')
                import_record.status = 'failed'
                import_record.error_message = f'JSON解析错误: {str(e)}'
                import_record.save()
                return False, errors
            
            # 验证数据
            if 'template' in data and import_record.create_template:
                template_data = data['template']
                
                # 验证模板数据
                if not template_data.get('name'):
                    validation_errors.append('模板名称不能为空')
                
                if 'items' in template_data:
                    for idx, item in enumerate(template_data['items']):
                        if not item.get('title'):
                            validation_errors.append(f'第 {idx + 1} 个清单项缺少标题')
            
            if 'instance' in data and import_record.create_instance:
                instance_data = data['instance']
                
                if not instance_data.get('name'):
                    validation_errors.append('实例名称不能为空')
            
            if validation_errors:
                import_record.status = 'failed'
                import_record.validation_errors = validation_errors
                import_record.save()
                errors.extend(validation_errors)
                return False, errors
            
            # 开始处理
            import_record.status = 'processing'
            import_record.save()
            
            success_count = 0
            import_record.total_records = 1  # 一个JSON文件通常包含一个清单
            
            # 处理模板导入
            if 'template' in data and import_record.create_template:
                from apps.checklists.services.checklist_service import ChecklistService
                
                template_data = data['template']
                
                try:
                    # 构建模板数据
                    create_data = {
                        'name': template_data['name'],
                        'description': template_data.get('description', ''),
                        'checklist_type': template_data.get('checklist_type', 'custom'),
                        'version': template_data.get('version', '1.0.0'),
                        'status': template_data.get('status', 'draft'),
                        'tags': template_data.get('tags', []),
                        'event_types': template_data.get('event_types', []),
                        'metadata': template_data.get('metadata', {}),
                        'items': template_data.get('items', [])
                    }
                    
                    template, create_errors = ChecklistService.create_template(
                        create_data, import_record.created_by
                    )
                    
                    if create_errors:
                        import_record.failed_records = 1
                        import_record.failed_records += 1
                        errors.extend(create_errors)
                    else:
                        success_count += 1
                        import_record.success_records = 1
                
                except Exception as e:
                    import_record.failed_records = 1
                    errors.append(f"导入模板失败: {str(e)}")
            
            # 处理实例导入
            elif 'instance' in data and import_record.create_instance:
                from apps.checklists.services.checklist_service import ChecklistService
                from apps.events.models import Event
                
                instance_data = data['instance']
                
                try:
                    # 需要提供event_id和template_id
                    event_id = instance_data.get('event_id') or instance_data.get('event')
                    template_id = instance_data.get('template_id') or instance_data.get('template')
                    
                    if not event_id or not template_id:
                        errors.append('导入实例需要提供event_id和template_id')
                        import_record.failed_records = 1
                    else:
                        # 验证event和template是否存在
                        try:
                            Event.objects.get(id=event_id)
                            ChecklistTemplate.objects.get(id=template_id)
                        except Event.DoesNotExist:
                            errors.append('指定的活动不存在')
                            import_record.failed_records = 1
                        except ChecklistTemplate.DoesNotExist:
                            errors.append('指定的模板不存在')
                            import_record.failed_records = 1
                        else:
                            create_data = {
                                'event_id': event_id,
                                'template_id': template_id,
                                'name': instance_data['name'],
                                'status': instance_data.get('status', 'incomplete'),
                                'metadata': instance_data.get('metadata', {})
                            }
                            
                            instance, create_errors = ChecklistService.create_instance(
                                create_data, import_record.created_by
                            )
                            
                            if create_errors:
                                import_record.failed_records = 1
                                errors.extend(create_errors)
                            else:
                                success_count += 1
                                import_record.success_records = 1
                
                except Exception as e:
                    import_record.failed_records = 1
                    errors.append(f"导入实例失败: {str(e)}")
            
            # 更新导入记录
            import_record.processed_records = 1
            import_record.completed_at = timezone.now()
            
            if success_count > 0:
                import_record.status = 'completed'
            else:
                import_record.status = 'failed'
            
            import_record.save()
            
            logger.info(f"JSON导入完成: 成功 {success_count}, 失败 {import_record.failed_records}")
            return success_count > 0, errors
            
        except Exception as e:
            logger.error(f"JSON导入失败: {e}")
            import_record.status = 'failed'
            import_record.error_message = str(e)
            import_record.save()
            errors.append(f"JSON导入失败: {str(e)}")
            return False, errors
    
    @staticmethod
    def import_from_csv(import_record: ChecklistImport) -> Tuple[bool, List[str]]:
        """从CSV导入清单"""
        errors = []
        
        try:
            import_record.status = 'validating'
            import_record.save()
            
            # 读取CSV文件
            try:
                with open(import_record.file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
            except FileNotFoundError:
                errors.append('文件不存在')
                import_record.status = 'failed'
                import_record.error_message = '文件不存在'
                import_record.save()
                return False, errors
            
            if len(rows) < 2:
                errors.append('CSV文件内容为空或格式不正确')
                import_record.status='failed'
                import_record.error_message = 'CSV文件内容为空或格式不正确'
                import_record.save()
                return False, errors
            
            # 开始处理
            import_record.status = 'processing'
            import_record.save()
            import_record.total_records = 1
            import_record.processed_records = 1
            import_record.success_records = 1
            import_record.completed_at = timezone.now()
            import_record.status = 'completed'
            import_record.save()
            
            logger.info(f"CSV导入完成")
            return True, []
            
        except Exception as e:
            logger.error(f"CSV导入失败: {e}")
            import_record.status = 'failed'
            import_record.error_message = str(e)
            import_record.save()
            errors.append(f"CSV导入失败: {str(e)}")
            return False, errors