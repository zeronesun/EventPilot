<!-- 交互历史管理组件 -->
<template>
  <div class="interactions-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>交互历史</h3>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            记录交互
          </el-button>
        </div>
      </template>

      <!-- 交互类型过滤 -->
      <div class="filter-section">
        <el-select
          v-model="selectedType"
          placeholder="选择交互类型"
          clearable
          @change="filterInteractions"
        >
          <el-option label="全部" value="" />
          <el-option
            v-for="type in interactionTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
      </div>

      <!-- 交互历史时间线 -->
      <div v-loading="loading" class="interactions-list">
        <el-empty v-if="!loading && filteredInteractions.length === 0" description="暂无交互记录" />

        <el-timeline v-else>
          <el-timeline-item
            v-for="interaction in filteredInteractions"
            :key="interaction.id"
            :timestamp="formatDateTime(interaction.interaction_date)"
            placement="top"
          >
            <div class="interaction-item">
              <div class="interaction-header">
                <el-tag :type="getInteractionTypeColor(interaction.interaction_type)" size="small">
                  {{ interaction.interaction_type_display }}
                </el-tag>
                <span class="interaction-title">{{ interaction.title }}</span>

                <!-- 满意度评分 -->
                <div v-if="interaction.satisfaction_score" class="satisfaction-score">
                  <el-rate
                    v-model="interaction.satisfaction_score"
                    disabled
                    show-score
                    text-color="#ff9900"
                  />
                </div>
              </div>

              <div class="interaction-content">
                <p>{{ interaction.description }}</p>
              </div>

              <!-- 元数据显示 -->
              <div v-if="hasMetadata(interaction)" class="interaction-metadata">
                <el-collapse>
                  <el-collapse-item title="详细信息" name="details">
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="关联活动">
                        {{ interaction.related_event_id || '无' }}
                      </el-descriptions-item>
                      <el-descriptions-item label="关联项目">
                        {{ interaction.related_project_id || '无' }}
                      </el-descriptions-item>
                      <el-descriptions-item label="结果状态">
                        <el-tag v-if="interaction.outcome_status" size="small" type="info">
                          {{ interaction.outcome_status }}
                        </el-tag>
                        <span v-else>无</span>
                      </el-descriptions-item>
                      <el-descriptions-item label="记录时间">
                        {{ formatDateTime(interaction.created_at) }}
                      </el-descriptions-item>
                      <!-- 动态显示其他元数据 -->
                      <template v-for="(value, key) in interaction.metadata" :key="key">
                        <el-descriptions-item
                          v-if="shouldDisplayMetadata(key)"
                          :label="formatMetadataKey(key)"
                        >
                          {{ formatMetadataValue(value) }}
                        </el-descriptions-item>
                      </template>
                    </el-descriptions>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- 操作按钮 -->
              <div class="interaction-actions">
                <el-button size="small" @click="editInteraction(interaction)"> 编辑 </el-button>
                <el-button size="small" type="danger" @click="deleteInteraction(interaction)">
                  删除
                </el-button>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>

    <!-- 添加/编辑交互对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingInteraction ? '编辑交互记录' : '记录新交互'"
      width="700px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="interactionForm" :rules="formRules" label-width="120px">
        <el-form-item label="交互类型" prop="interaction_type">
          <el-select
            v-model="interactionForm.interaction_type"
            placeholder="选择交互类型"
            style="width: 100%"
          >
            <el-option
              v-for="type in interactionTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input v-model="interactionForm.title" placeholder="请输入交互标题" />
        </el-form-item>

        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="interactionForm.description"
            type="textarea"
            :rows="4"
            placeholder="请详细描述此次交互的内容"
          />
        </el-form-item>

        <el-form-item label="满意度评分" prop="satisfaction_score">
          <el-rate
            v-model="interactionForm.satisfaction_score"
            show-score
            text-color="#ff9900"
            :texts="['非常不满意', '不满意', '一般', '满意', '非常满意']"
          />
        </el-form-item>

        <el-form-item label="结果状态" prop="outcome_status">
          <el-select
            v-model="interactionForm.outcome_status"
            placeholder="选择结果状态"
            style="width: 100%"
            clearable
          >
            <el-option label="成功" value="successful" />
            <el-option label="部分成功" value="partially_successful" />
            <el-option label="失败" value="failed" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="取消" value="cancelled" />
          </el-select>
        </el-form-item>

        <el-form-item label="关联活动">
          <el-input v-model="interactionForm.related_event_id" placeholder="活动ID" />
        </el-form-item>

        <el-form-item label="关联项目">
          <el-input v-model="interactionForm.related_project_id" placeholder="项目ID" />
        </el-form-item>

        <el-divider content-position="left">扩展信息</el-divider>

        <!-- 动态元数据字段 -->
        <el-form-item label="金额（元）">
          <el-input-number
            v-model="interactionForm.metadata.amount"
            :min="0"
            :precision="2"
            placeholder="业务金额"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="参与人员">
          <el-input v-model="interactionForm.metadata.participants" placeholder="参与人员名单" />
        </el-form-item>

        <el-form-item label="地点">
          <el-input v-model="interactionForm.metadata.location" placeholder="交互地点" />
        </el-form-item>

        <el-form-item label="下一步计划">
          <el-input
            v-model="interactionForm.metadata.next_steps"
            type="textarea"
            :rows="2"
            placeholder="后续行动计划"
          />
        </el-form-item>

        <!-- 交互时间 -->
        <el-form-item label="交互时间" prop="interaction_date">
          <el-date-picker
            v-model="interactionForm.interaction_date"
            type="datetime"
            placeholder="选择交互时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useProfilesStore } from '@/stores/profiles';
import type { InteractionHistory } from '@/lib/profiles-client';

const props = defineProps<{
  profileId: string;
}>();

const profilesStore = useProfilesStore();

// 交互类型定义
const interactionTypes = [
  { label: '活动合作', value: 'event' },
  { label: '合同签署', value: 'contract' },
  { label: '沟通联系', value: 'communication' },
  { label: '会议交流', value: 'meeting' },
  { label: '付款', value: 'payment' },
  { label: '支持服务', value: 'support' },
  { label: '投诉处理', value: 'complaint' },
  { label: '商务谈判', value: 'negotiation' },
  { label: '其他', value: 'other' },
];

// 响应式数据
const loading = ref(true);
const selectedType = ref('');
const interactions = ref<InteractionHistory[]>([]);

// 对话框相关
const showAddDialog = ref(false);
const editingInteraction = ref<InteractionHistory | null>(null);
const formRef = ref();
const interactionForm = ref({
  interaction_type: 'communication',
  title: '',
  description: '',
  satisfaction_score: 3,
  outcome_status: '',
  related_event_id: '',
  related_project_id: '',
  interaction_date: new Date(),
  metadata: {
    amount: undefined,
    participants: '',
    location: '',
    next_steps: '',
  },
});

// 表单验证规则
const formRules = {
  interaction_type: [{ required: true, message: '请选择交互类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入交互标题', trigger: 'blur' }],
  description: [{ required: true, message: '请输入详细描述', trigger: 'blur' }],
  interaction_date: [
    {
      required: true,
      message: '请选择交互时间',
      trigger: 'change',
    },
  ],
};

// 过滤后的交互列表
const filteredInteractions = computed(() => {
  if (!selectedType.value) {
    return interactions.value;
  }
  return interactions.value.filter(
    (interaction) => interaction.interaction_type === selectedType.value
  );
});

// 加载交互历史
const loadInteractions = async () => {
  loading.value = true;
  try {
    const result = await profilesStore.selectProfile(props.profileId);
    if (result) {
      interactions.value = profilesStore.interactions || [];
    }
  } catch (error) {
    console.error('加载交互历史失败:', error);
    ElMessage.error('加载交互历史失败');
  } finally {
    loading.value = false;
  }
};

// 过滤交互
const filterInteractions = () => {
  // 过滤逻辑由计算属性处理
};

// 获取交互类型颜色
const getInteractionTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    event: 'success',
    contract: 'warning',
    communication: 'info',
    meeting: 'primary',
    payment: 'success',
    support: 'info',
    complaint: 'danger',
    negotiation: 'warning',
    other: '',
  };
  return colorMap[type] || '';
};

// 检查是否有元数据
const hasMetadata = (interaction: InteractionHistory) => {
  return interaction.metadata && Object.keys(interaction.metadata).length > 0;
};

// 判断是否应该显示元数据字段
const shouldDisplayMetadata = (key: string) => {
  const skipKeys = ['amount', 'participants', 'location', 'next_steps'];
  return !skipKeys.includes(key);
};

// 格式化元数据键名
const formatMetadataKey = (key: string) => {
  const keyMap: Record<string, string> = {
    document: '相关文档',
    duration: '持续时间',
    outcome: '具体结果',
    issues: '存在问题',
    solutions: '解决方案',
  };
  return keyMap[key] || key;
};

// 格式化元数据值
const formatMetadataValue = (value: unknown) => {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
};

// 编辑交互
const editInteraction = (interaction: InteractionHistory) => {
  editingInteraction.value = interaction;
  interactionForm.value = {
    interaction_type: interaction.interaction_type,
    title: interaction.title,
    description: interaction.description,
    satisfaction_score: interaction.satisfaction_score || 3,
    outcome_status: interaction.outcome_status || '',
    related_event_id: interaction.related_event_id || '',
    related_project_id: interaction.related_project_id || '',
    interaction_date: new Date(interaction.interaction_date),
    metadata: {
      amount: interaction.metadata.amount,
      participants: interaction.metadata.participants || '',
      location: interaction.metadata.location || '',
      next_steps: interaction.metadata.next_steps || '',
    },
  };
  showAddDialog.value = true;
};

// 删除交互
const deleteInteraction = (interaction: InteractionHistory) => {
  ElMessageBox.confirm(`确定要删除交互记录 "${interaction.title}" 吗？`, '确认删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        // 这里应该调用删除API，目前先从本地状态移除
        interactions.value = interactions.value.filter((i) => i.id !== interaction.id);
        ElMessage.success('删除成功');
      } catch (error) {
        console.error('删除交互记录失败:', error);
        ElMessage.error('删除交互记录失败');
      }
    })
    .catch(() => {
      // 用户取消删除
    });
};

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate();

    const interactionData = {
      ...interactionForm.value,
      interaction_date: interactionForm.value.interaction_date.toISOString(),
    };

    if (editingInteraction.value) {
      // 更新交互
      // 需要实现updateInteraction API
      ElMessage.info('更新功能开发中');
      showAddDialog.value = false;
    } else {
      // 创建交互
      const result = await profilesStore.addInteraction(props.profileId, interactionData);

      if (typeof result === 'object' && 'success' in result) {
        if (result.success) {
          ElMessage.success('记录成功');
          showAddDialog.value = false;
          await loadInteractions();
        } else {
          ElMessage.error(result.error || '记录失败');
        }
      } else if (result) {
        ElMessage.success('记录成功');
        showAddDialog.value = false;
        await loadInteractions();
      } else {
        ElMessage.error('记录失败');
      }
    }
  } catch (error) {
    console.error('提交表单失败:', error);
    ElMessage.error('操作失败，请检查输入');
  }
};

// 重置表单
const resetForm = () => {
  editingInteraction.value = null;
  interactionForm.value = {
    interaction_type: 'communication',
    title: '',
    description: '',
    satisfaction_score: 3,
    outcome_status: '',
    related_event_id: '',
    related_project_id: '',
    interaction_date: new Date(),
    metadata: {
      amount: undefined,
      participants: '',
      location: '',
      next_steps: '',
    },
  };
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 组件挂载时加载交互历史
onMounted(() => {
  loadInteractions();
});
</script>

<style scoped>
.interactions-manager {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-section {
  margin-bottom: 20px;
}

.interactions-list {
  min-height: 400px;
  padding: 20px 0;
}

.interaction-item {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.interaction-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.interaction-title {
  font-weight: 600;
  color: #303133;
}

.satisfaction-score {
  margin-left: auto;
}

.interaction-content {
  margin-bottom: 12px;
}

.interaction-content p {
  color: #606266;
  line-height: 1.6;
}

.interaction-metadata {
  margin-bottom: 12px;
}

.interactions-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
