<template>
  <el-dialog
    v-model="isOpen"
    title="批量编辑活动"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="batch-edit-content">
      <!-- 选中数量提示 -->
      <el-alert
        :title="`已选择 ${events.length} 个活动`"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <template #default>
          <div class="selected-events-preview">
            <el-tag
              v-for="event in previewEvents"
              :key="event.id"
              size="small"
              style="margin: 4px"
            >
              {{ event.name }}
            </el-tag>
            <el-tag v-if="events.length > previewLimit" type="info" size="small">
              +{{ events.length - previewLimit }}
            </el-tag>
          </div>
        </template>
      </el-alert>

      <!-- 批量编辑表单 -->
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="活动类型">
          <el-select
            v-model="formData.type"
            placeholder="选择修改类型（留空则不修改）"
            clearable
            style="width: 100%"
          >
            <el-option label="会议" value="conference" />
            <el-option label="培训" value="training" />
            <el-option label="活动" value="event" />
            <el-option label="团建" value="team_building" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="活动状态">
          <el-select
            v-model="formData.status"
            placeholder="选择修改状态（留空则不修改）"
            clearable
            style="width: 100%"
          >
            <el-option label="策划中" value="planning" />
            <el-option label="执行中" value="executing" />
            <el-option label="已完成" value="completed" />
            <el-option label="已复盘" value="reviewed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>

        <el-form-item label="负责人">
          <el-select
            v-model="formData.owner_name"
            placeholder="选择或输入负责人（留空则不修改）"
            clearable
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="owner in uniqueOwners"
              :key="owner"
              :label="owner"
              :value="owner"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="活动地点">
          <el-input
            v-model="formData.location"
            placeholder="输入地点（留空则不修改）"
            clearable
          />
        </el-form-item>

        <el-form-item label="预算备注">
          <el-input
            v-model="formData.budget_note"
            type="textarea"
            :rows="2"
            placeholder="输入备注（留空则不修改）"
          />
        </el-form-item>
      </el-form>

      <el-alert
        title="注意"
        type="warning"
        :closable="false"
        style="margin-top: 16px"
      >
        留空的字段不会被修改
      </el-alert>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          保存修改
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  events: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const isOpen = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const previewLimit = 3

const formData = ref({
  type: '',
  status: '',
  owner_name: '',
  location: '',
  budget_note: ''
})

const formRules = {}

// 预览选中的活动
const previewEvents = computed(() => {
  return props.events.slice(0, previewLimit)
})

// 提取不重复的负责人列表
const uniqueOwners = computed(() => {
  const owners = new Set()
  props.events.forEach(event => {
    if (event.owner_name) {
      owners.add(event.owner_name)
    }
  })
  return Array.from(owners).sort()
})

// 监听外部控制
watch(() => props.modelValue, (val) => {
  isOpen.value = val
})

watch(isOpen, (val) => {
  emit('update:modelValue', val)
  if (val) {
    resetForm()
  }
})

function resetForm() {
  formData.value = {
    type: '',
    status: '',
    owner_name: '',
    location: '',
    budget_note: ''
  }
}

async function handleSubmit() {
  if (submitting.value) return

  // 检查是否有字段被修改
  const hasChanges = Object.values(formData.value).some(
    value => value !== ''
  )

  if (!hasChanges) {
    ElMessage.warning('请至少选择一个字段进行修改')
    return
  }

  submitting.value = true

  try {
    // 只提交非空字段
    const updateData = {}
    for (const [key, value] of Object.entries(formData.value)) {
      if (value !== '') {
        updateData[key] = value
      }
    }

    // 调用批量更新
    const eventIds = props.events.map(e => e.id)

    emit('success', {
      ids: eventIds,
      data: updateData
    })

    ElMessage.success(`成功更新 ${eventIds.length} 个活动`)
    handleClose()
  } catch (error) {
    console.error('Batch update failed:', error)
    ElMessage.error('批量更新失败')
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  isOpen.value = false
}
</script>

<style scoped>
.batch-edit-content {
  padding: 8px 0;
}

.selected-events-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
