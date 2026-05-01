<!-- 评估系统组件 -->
<template>
  <div class="evaluations-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>评估评级</h3>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            创建评估
          </el-button>
        </div>
      </template>

      <!-- 评估统计卡片 -->
      <div class="stats-cards">
        <div class="stat-card">
          <div class="stat-label">平均信用评分</div>
          <div class="stat-value">{{ avgScores.credit }}</div>
          <div class="stat-bar">
            <el-progress :percentage="avgScores.credit" :color="getScoreColor(avgScores.credit)" />
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">平均质量评分</div>
          <div class="stat-value">{{ avgScores.quality }}</div>
          <div class="stat-bar">
            <el-progress
              :percentage="avgScores.quality"
              :color="getScoreColor(avgScores.quality)"
            />
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">平均综合评分</div>
          <div class="stat-value">{{ avgScores.overall }}</div>
          <div class="stat-bar">
            <el-progress
              :percentage="avgScores.overall"
              :color="getScoreColor(avgScores.overall)"
            />
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">评估次数</div>
          <div class="stat-value">{{ evaluations.length }}</div>
          <div class="stat-label">次</div>
        </div>
      </div>

      <!-- 评估记录列表 -->
      <div v-loading="loading" class="evaluations-list">
        <el-empty v-if="!loading && evaluations.length === 0" description="暂无评估记录" />

        <div v-else class="evaluation-timeline">
          <div v-for="evaluation in evaluations" :key="evaluation.id" class="evaluation-item">
            <div class="evaluation-header">
              <div class="evaluation-info">
                <div class="evaluator-name">
                  <el-icon><User /></el-icon>
                  {{ evaluation.evaluator_name }}
                </div>
                <div class="evaluation-date">
                  <el-icon><Calendar /></el-icon>
                  {{ formatDate(evaluation.evaluation_date) }}
                </div>
              </div>

              <div class="evaluation-scores">
                <el-tooltip content="信用评分">
                  <div class="score-badge" :class="getScoreClass(evaluation.credit_score || 0)">
                    信用: {{ evaluation.credit_score || 0 }}
                  </div>
                </el-tooltip>
                <el-tooltip content="质量评分">
                  <div class="score-badge" :class="getScoreClass(evaluation.quality_score || 0)">
                    质量: {{ evaluation.quality_score || 0 }}
                  </div>
                </el-tooltip>
                <el-tooltip content="风险等级">
                  <el-tag :type="getRiskType(evaluation.risk_level)" size="small">
                    {{ getRiskText(evaluation.risk_level) }}
                  </el-tag>
                </el-tooltip>
              </div>
            </div>

            <div class="evaluation-body">
              <div class="dimension-scores">
                <div class="dimension-item">
                  <span class="dimension-label">服务质量:</span>
                  <el-rate
                    v-model="evaluation.service_quality"
                    disabled
                    show-score
                    text-color="#ff9900"
                  />
                </div>
                <div class="dimension-item">
                  <span class="dimension-label">响应速度:</span>
                  <el-rate
                    v-model="evaluation.response_speed"
                    disabled
                    show-score
                    text-color="#ff9900"
                  />
                </div>
                <div class="dimension-item">
                  <span class="dimension-label">专业能力:</span>
                  <el-rate
                    v-model="evaluation.professional_ability"
                    disabled
                    show-score
                    text-color="#ff9900"
                  />
                </div>
              </div>

              <div v-if="evaluation.risk_assessment" class="risk-assessment">
                <div class="assessment-label">风险评估:</div>
                <p>{{ evaluation.risk_assessment }}</p>
              </div>

              <div v-if="evaluation.recommendations" class="recommendations">
                <div class="assessment-label">改进建议:</div>
                <p>{{ evaluation.recommendations }}</p>
              </div>

              <div v-if="evaluation.overall_conclusion" class="overall-conclusion">
                <div class="assessment-label">总体结论:</div>
                <p>{{ evaluation.overall_conclusion }}</p>
              </div>

              <div v-if="evaluation.next_evaluation_date" class="next-evaluation">
                <el-icon><Clock /></el-icon>
                下次评估: {{ formatDate(evaluation.next_evaluation_date) }}
              </div>
            </div>

            <div class="evaluation-footer">
              <el-button size="small" @click="viewDetails(evaluation)"> 查看详情 </el-button>
              <el-button size="small" @click="editEvaluation(evaluation)"> 编辑 </el-button>
              <el-button size="small" type="danger" @click="deleteEvaluation(evaluation)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建/编辑评估对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingEvaluation ? '编辑评估' : '创建评估'"
      width="800px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="evaluationForm" :rules="formRules" label-width="120px">
        <el-divider content-position="left">评分输入</el-divider>

        <div class="scores-input">
          <el-form-item label="信用评分" prop="credit_score">
            <el-slider
              v-model="evaluationForm.credit_score"
              :step="1"
              :max="100"
              show-input
              :marks="{ 0: '差', 50: '良', 100: '优' }"
            />
          </el-form-item>

          <el-form-item label="质量评分" prop="quality_score">
            <el-slider
              v-model="evaluationForm.quality_score"
              :step="1"
              :max="100"
              show-input
              :marks="{ 0: '差', 50: '良', 100: '优' }"
            />
          </el-form-item>
        </div>

        <el-divider content-position="left">子维度评估</el-divider>

        <div class="dimension-inputs">
          <el-form-item label="服务质量" prop="service_quality">
            <el-rate
              v-model="evaluationForm.service_quality"
              show-score
              text-color="#ff9900"
              :texts="['很差', '较差', '一般', '较好', '优秀']"
            />
          </el-form-item>

          <el-form-item label="响应速度" prop="response_speed">
            <el-rate
              v-model="evaluationForm.response_speed"
              show-score
              text-color="#ff9900"
              :texts="['很慢', '较慢', '一般', '较快', '太快']"
            />
          </el-form-item>

          <el-form-item label="专业能力" prop="professional_ability">
            <el-rate
              v-model="evaluationForm.professional_ability"
              show-score
              text-color="#ff9900"
              :texts="['很弱', '较弱', '一般', '较强', '很强']"
            />
          </el-form-item>
        </div>

        <el-divider content-position="left">风险评估</el-divider>

        <el-form-item label="风险等级" prop="risk_level">
          <el-radio-group v-model="evaluationForm.risk_level">
            <el-radio label="low">低风险</el-radio>
            <el-radio label="medium">中风险</el-radio>
            <el-radio label="high">高风险</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="风险评估报告">
          <el-input
            v-model="evaluationForm.risk_assessment"
            type="textarea"
            :rows="4"
            placeholder="请详细描述风险评估内容"
          />
        </el-form-item>

        <el-divider content-position="left">分析建议</el-divider>

        <el-form-item label="改进建议" prop="recommendations">
          <el-input
            v-model="evaluationForm.recommendations"
            type="textarea"
            :rows="4"
            placeholder="请提出改进意见和建议"
          />
        </el-form-item>

        <el-form-item label="总体结论">
          <el-input
            v-model="evaluationForm.overall_conclusion"
            type="textarea"
            :rows="3"
            placeholder="请总结总体评估结论"
          />
        </el-form-item>

        <el-form-item label="下次评估时间">
          <el-date-picker
            v-model="evaluationForm.next_evaluation_date"
            type="date"
            placeholder="选择下次评估日期"
            style="width: 100%"
          />
        </el-form-item>

        <!-- 自定义评估标准 -->
        <el-divider content-position="left">评估标准设置</el-divider>

        <el-form-item label="评估标准">
          <el-collapse>
            <el-collapse-item title="配置评估标准" name="criteria">
              <div class="criteria-config">
                <el-form-item label="服务权重">
                  <el-slider
                    v-model="evaluationForm.evaluation_criteria.service_weight"
                    :max="100"
                  />
                </el-form-item>
                <el-form-item label="响应权重">
                  <el-slider
                    v-model="evaluationForm.evaluation_criteria.response_weight"
                    :max="100"
                  />
                </el-form-item>
                <el-form-item label="专业权重">
                  <el-slider
                    v-model="evaluationForm.evaluation_criteria.professional_weight"
                    :max="100"
                  />
                </el-form-item>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 评估详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="评估详情" width="700px">
      <div v-if="selectedEvaluation" class="evaluation-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="评估人">
            {{ selectedEvaluation.evaluator_name }}
          </el-descriptions-item>
          <el-descriptions-item label="评估日期">
            {{ formatDate(selectedEvaluation.evaluation_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="信用评分" :span="2">
            <el-progress
              :percentage="selectedEvaluation.credit_score || 0"
              :color="getScoreColor(selectedEvaluation.credit_score || 0)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="质量评分" :span="2">
            <el-progress
              :percentage="selectedEvaluation.quality_score || 0"
              :color="getScoreColor(selectedEvaluation.quality_score || 0)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="服务质量">
            <el-rate :model-value="selectedEvaluation.service_quality" disabled show-score />
          </el-descriptions-item>
          <el-descriptions-item label="响应速度">
            <el-rate :model-value="selectedEvaluation.response_speed" disabled show-score />
          </el-descriptions-item>
          <el-descriptions-item label="专业能力" :span="2">
            <el-rate :model-value="selectedEvaluation.professional_ability" disabled show-score />
          </el-descriptions-item>
          <el-descriptions-item label="风险等级">
            <el-tag :type="getRiskType(selectedEvaluation.risk_level)">
              {{ getRiskText(selectedEvaluation.risk_level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下次评估">
            {{ formatDate(selectedEvaluation.next_evaluation_date) }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedEvaluation.risk_assessment" class="detail-section">
          <h4>风险评估报告</h4>
          <p>{{ selectedEvaluation.risk_assessment }}</p>
        </div>

        <div v-if="selectedEvaluation.recommendations" class="detail-section">
          <h4>改进建议</h4>
          <p>{{ selectedEvaluation.recommendations }}</p>
        </div>

        <div v-if="selectedEvaluation.overall_conclusion" class="detail-section">
          <h4>总体结论</h4>
          <p>{{ selectedEvaluation.overall_conclusion }}</p>
        </div>

        <div class="detail-section">
          <h4>评估标准</h4>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item
              v-for="(value, key) in selectedEvaluation.evaluation_criteria"
              :key="key"
              :label="formatCriteriaKey(key)"
            >
              {{ value }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, User, Calendar, Clock } from '@element-plus/icons-vue';
import { useProfilesStore } from '@/stores/profiles';
import type { ProfileEvaluation } from '@/lib/profiles-client';

const props = defineProps<{
  profileId: string;
}>();

const profilesStore = useProfilesStore();

// 响应式数据
const loading = ref(true);
const evaluations = ref<ProfileEvaluation[]>([]);
const selectedEvaluation = ref<ProfileEvaluation | null>(null);

// 对话框控制
const showAddDialog = ref(false);
const showDetailDialog = ref(false);
const editingEvaluation = ref<ProfileEvaluation | null>(null);
const formRef = ref();

// 表单数据
const evaluationForm = ref({
  credit_score: 70,
  quality_score: 70,
  service_quality: 3,
  response_speed: 3,
  professional_ability: 3,
  risk_level: 'medium',
  risk_assessment: '',
  recommendations: '',
  overall_conclusion: '',
  next_evaluation_date: new Date(),
  evaluation_criteria: {
    service_weight: 33,
    response_weight: 33,
    professional_weight: 34,
  },
});

// 表单验证规则
const formRules = {
  credit_score: [{ required: true, message: '请输入信用评分', trigger: 'blur' }],
  quality_score: [{ required: true, message: '请输入质量评分', trigger: 'blur' }],
  service_quality: [{ required: true, message: '请评估服务质量', trigger: 'change' }],
  response_speed: [{ required: true, message: '请评估响应速度', trigger: 'change' }],
  professional_ability: [{ required: true, message: '请评估专业能力', trigger: 'change' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
};

// 计算平均分数
const avgScores = computed(() => {
  if (evaluations.value.length === 0) {
    return { credit: 0, quality: 0, overall: 0 };
  }

  const creditSum = evaluations.value.reduce((sum, e) => sum + (e.credit_score || 0), 0);
  const qualitySum = evaluations.value.reduce((sum, e) => sum + (e.quality_score || 0), 0);
  const overallSum = evaluations.value.reduce(
    (sum, e) => sum + ((e.credit_score || 0) + (e.quality_score || 0)) / 2,
    0
  );

  const count = evaluations.value.length;
  return {
    credit: Math.round(creditSum / count),
    quality: Math.round(qualitySum / count),
    overall: Math.round(overallSum / count),
  };
});

// 加载评估记录
const loadEvaluations = async () => {
  loading.value = true;
  try {
    const result = await profilesStore.selectProfile(props.profileId);
    if (result) {
      evaluations.value = profilesStore.evaluations || [];
    }
  } catch (error) {
    console.error('加载评估记录失败:', error);
    ElMessage.error('加载评估记录失败');
  } finally {
    loading.value = false;
  }
};

// 获取分数对应的颜色
const getScoreColor = (score: number) => {
  if (score >= 80) return '#67C23A';
  if (score >= 60) return '#409EFF';
  if (score >= 40) return '#E6A23C';
  return '#F56C6C';
};

// 获取分数对应的CSS类
const getScoreClass = (score: number) => {
  if (score >= 80) return 'high-score';
  if (score >= 60) return 'medium-score';
  if (score >= 40) return 'low-score';
  return 'very-low-score';
};

// 获取风险等级类型
const getRiskType = (level: string) => {
  const typeMap: Record<string, string> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
  };
  return typeMap[level] || 'info';
};

// 获取风险等级文本
const getRiskText = (level: string) => {
  const textMap: Record<string, string> = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  };
  return textMap[level] || level;
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('zh-CN');
};

// 格式化评估标准键名
const formatCriteriaKey = (key: string) => {
  const keyMap: Record<string, string> = {
    service_weight: '服务权重',
    response_weight: '响应权重',
    professional_weight: '专业权重',
  };
  return keyMap[key] || key;
};

// 查看详情
const viewDetails = (evaluation: ProfileEvaluation) => {
  selectedEvaluation.value = evaluation;
  showDetailDialog.value = true;
};

// 编辑评估
const editEvaluation = (evaluation: ProfileEvaluation) => {
  editingEvaluation.value = evaluation;
  evaluationForm.value = {
    credit_score: evaluation.credit_score || 70,
    quality_score: evaluation.quality_score || 70,
    service_quality: evaluation.service_quality || 3,
    response_speed: evaluation.response_speed || 3,
    professional_ability: evaluation.professional_ability || 3,
    risk_level: evaluation.risk_level,
    risk_assessment: evaluation.risk_assessment || '',
    recommendations: evaluation.recommendations || '',
    overall_conclusion: evaluation.overall_conclusion || '',
    next_evaluation_date: evaluation.next_evaluation_date
      ? new Date(evaluation.next_evaluation_date)
      : new Date(),
    evaluation_criteria: evaluation.evaluation_criteria || {
      service_weight: 33,
      response_weight: 33,
      professional_weight: 34,
    },
  };
  showAddDialog.value = true;
};

// 删除评估
const deleteEvaluation = (evaluation: ProfileEvaluation) => {
  ElMessageBox.confirm(`确定要删除此次评估记录吗？`, '确认删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        // 这里应该调用删除API，目前先从本地状态移除
        evaluations.value = evaluations.value.filter((e) => e.id !== evaluation.id);
        ElMessage.success('删除成功');
      } catch (error) {
        console.error('删除评估记录失败:', error);
        ElMessage.error('删除评估记录失败');
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

    const evaluationData = {
      ...evaluationForm.value,
      next_evaluation_date: evaluationForm.value.next_evaluation_date.toISOString(),
    };

    if (editingEvaluation.value) {
      // 更新评估
      ElMessage.info('更新功能开发中');
      showAddDialog.value = false;
    } else {
      // 创建评估
      const result = await profilesStore.addEvaluation(props.profileId, evaluationData);

      if (typeof result === 'object' && 'success' in result) {
        if (result.success) {
          ElMessage.success('评估创建成功');
          showAddDialog.value = false;
          await loadEvaluations();
        } else {
          ElMessage.error(result.error || '创建失败');
        }
      } else if (result) {
        ElMessage.success('评估创建成功');
        showAddDialog.value = false;
        await loadEvaluations();
      } else {
        ElMessage.error('创建失败');
      }
    }
  } catch (error) {
    console.error('提交表单失败:', error);
    ElMessage.error('操作失败，请检查输入');
  }
};

// 重置表单
const resetForm = () => {
  editingEvaluation.value = null;
  evaluationForm.value = {
    credit_score: 70,
    quality_score: 70,
    service_quality: 3,
    response_speed: 3,
    professional_ability: 3,
    risk_level: 'medium',
    risk_assessment: '',
    recommendations: '',
    overall_conclusion: '',
    next_evaluation_date: new Date(),
    evaluation_criteria: {
      service_weight: 33,
      response_weight: 33,
      professional_weight: 34,
    },
  };
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

// 组件挂载时加载评估记录
onMounted(() => {
  loadEvaluations();
});
</script>

<style scoped>
.evaluations-manager {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.evalulations-list {
  min-height: 400px;
}

.evaluation-timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.evaluation-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.evaluation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.evaluation-info {
  display: flex;
  gap: 16px;
  align-items: center;
}

.evaluator-name,
.evaluation-date {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
}

.evaluation-scores {
  display: flex;
  gap: 12px;
  align-items: center;
}

.score-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.score-badge.high-score {
  background: #f0f9ff;
  color: #67c23a;
}

.score-badge.medium-score {
  background: #ecf5ff;
  color: #409eff;
}

.score-badge.low-score {
  background: #fef0f0;
  color: #e6a23c;
}

.score-badge.very-low-score {
  background: #fef0f0;
  color: #f56c6c;
}

.evaluation-body {
  padding: 20px;
}

.dimension-scores {
  margin-bottom: 16px;
}

.dimension-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.dimension-label {
  width: 100px;
  font-weight: 500;
  color: #303133;
}

.risk-assessment,
.recommendations,
.overall-conclusion {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-left: 3px solid #409eff;
  border-radius: 2px;
}

.assessment-label {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.risk-assessment p,
.recommendations p,
.overall-conclusion p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.next-evaluation {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #909399;
}

.evaluation-footer {
  padding: 12px 20px;
  background: #fafafa;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.scores-input {
  padding: 0 20px;
}

.dimension-inputs {
  padding: 0 20px;
}

.criteria-config {
  padding: 0 20px;
}

.evaluation-detail {
  margin-bottom: 20px;
}

.detail-section {
  margin-top: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.detail-section p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}
</style>
