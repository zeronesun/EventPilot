# EventPilot - 关联方档案管理系统 (Phase 3)

## 📋 模块概述

关联方档案管理系统用于管理客户、供应商、合作伙伴的完整档案，包括基本信息、联系人、交互历史、评估评级和智能推荐功能。

## 🎯 核心功能

1. **档案管理**: 创建、查看、更新、删除关联方档案
2. **联系人管理**: 管理主要联系人和联系方式
3. **交互历史**: 记录所有业务交互和合作记录
4. **评估评级**: 信用评分、质量评分、风险评估
5. **智能推荐**: 基于规则的档案推荐系统

## 🏗️ 架构设计

### 数据模型

- **ContactProfile**: 关联方档案主表
- **ContactPerson**: 联系人详情表
- **InteractionHistory**: 交互历史记录表
- **ProfileEvaluation**: 评估记录表

### API端点

```
POST /api/profiles/                    # 创建档案
GET  /api/profiles/                    # 档案列表
GET  /api/profiles/{id}/               # 档案详情
PUT  /api/profiles/{id}/               # 更新档案
DELETE /api/profiles/{id}/            # 删除档案
GET  /api/profiles/search/            # 智能搜索
POST /api/profiles/recommendations/   # 智能推荐
```

## 🔧 技术实现

遵循EventPilot现有架构模式：
- Django + DRF后端
- 三层架构：API Views → Services → Models
- JWT认证和权限管理
- 结构化日志和错误处理
- Pinia状态管理集成