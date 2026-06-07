# 更新验证问题修复

## 问题描述

在编辑活动、清单模板、清单实例等模块时，点击保存后会提示"更新失败"，后端返回400错误。

## 根本原因

更新操作使用的是 `UpdateSerializer`（部分更新，不包含所有字段），但Service层的验证函数却要求所有必填字段都必须存在。这导致在部分更新时会验证失败。

例如：
- `EventUpdateSerializer` 不包含 `end_date` 字段
- 但 `EventService.validate_event_data()` 却要求 `end_date` 不能为空
- 更新时前端发送的数据可能不包含某些字段，导致验证失败

## 修复方案

为所有Service层的验证函数添加 `partial` 参数，区分完整验证和部分更新验证：

1. **EventService** (`apps/events/services/event_service.py`)
   - 为 `validate_event_data()` 添加 `partial` 参数
   - 在 `update_event()` 中调用时传入 `partial=True`
   - 部分更新时不强制要求为空的字段

2. **ChecklistService** (`apps/checklists/services/checklist_service.py`)
   - 为 `validate_template_data()` 添加 `partial` 参数
   - 为 `validate_instance_data()` 添加 `partial` 参数
   - 在 `update_template()` 和 `update_instance()` 中调用时传入 `partial=True`

## 修改的文件

1. `apps/events/services/event_service.py`
2. `apps/checklists/services/checklist_service.py`

## 修复后的行为

- **创建操作**：`partial=False`，要求所有必填字段
- **更新操作**：`partial=True`，只验证提供的字段
- **验证逻辑**：
  ```python
  if field_value:
      # 存在字段，验证其值
      if not valid:
          add_error()
  elif not partial:
      # 字段不存在且不是部分更新，报错
      add_required_error()
  ```

## 测试验证

1. 启动后端服务
2. 在前端编辑活动，修改任意字段
3. 点击保存，应成功更新
4. 同样测试清单模板、清单实例的编辑

## 相关模块状态

- ✅ Events - 已修复
- ✅ Checklists - 已修复
- ℹ️ Tasks - 未验证，需检查是否有类似问题
- ℹ️ Users - 未验证，需检查是否有类似问题
- ℹ️ Files - 未验证，需检查是否有类似问题
