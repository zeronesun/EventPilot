<template>
  <el-dialog
    v-model="visible"
    title="新建活动"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-position="top"
    >
      <el-form-item label="活动名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入活动名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="活动类型" prop="type">
        <el-select v-model="formData.type" placeholder="请选择活动类型">
          <el-option label="会议" value="conference" />
          <el-option label="培训" value="training" />
          <el-option label="活动" value="event" />
          <el-option label="团建" value="team_building" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>

      <el-form-item label="活动描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          placeholder="请输入活动描述"
          :rows="3"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="开始时间" prop="start_date">
            <el-date-picker
              v-model="formData.start_date"
              type="datetime"
              placeholder="选择开始时间"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="结束时间" prop="end_date">
            <el-date-picker
              v-model="formData.end_date"
              type="datetime"
              placeholder="选择结束时间"
              style="width: 100%"
              format="YYYY-MM-DD HH:mm"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="预算金额" prop="budget">
        <el-input-number
          v-model="formData.budget"
          :min="0"
          :max="1000000"
          :step="100"
          placeholder="请输入预算金额"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio label="planning">策划中</el-radio>
          <el-radio label="executing">执行中</el-radio>
          <el-radio label="completed">已完成</el-radio>
          <el-radio label="reviewed">已复盘</el-radio>
          <el-radio label="cancelled">已取消</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="isLoading" @click="handleSubmit">
        创建
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventsStore } from '@/stores'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: boolean
  defaultStatus?: string
}

const props = withDefaults(defineProps<Props>(), {
  defaultStatus: 'pending'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const eventsStore = useEventsStore()
const formRef = ref<any>(null)
const isLoading = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formData = ref({
  name: '',
  type: '',
  description: '',
  start_date: '',
  end_date: '',
  budget: null,
  status: props.defaultStatus
})

const formRules = {
  name: [
    { required: true, message: '请输入活动名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择活动类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择活动状态', trigger: 'change' }
  ]
}

watch(() => props.defaultStatus, (newVal) => {
  formData.value.status = newVal || 'planning'
})

watch(() => props.modelValue, (newVal) => {
  if (!newVal) {
    resetForm()
  }
})

async function handleSubmit() {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    isLoading.value = true
    
    await eventsStore.createEvent(formData.value)
    
    ElMessage.success('活动创建成功')
    emit('success')
    visible.value = false
  } catch (error: any) {
    if (error !== false) {
      console.error('Create event failed:', error)
      ElMessage.error(error.message || '创建失败')
    }
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  formRef.value?.resetFields()
  formData.value = {
    name: '',
    type: '',
    description: '',
    start_date: '',
    end_date: '',
    budget: null,
    status: props.defaultStatus
  }
}
</script>

<style scoped>
:deep(.el-dialog__body) {
  padding: 20px;
}
</style>
