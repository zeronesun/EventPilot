<template>
  <el-dialog
    v-model="isOpen"
    :title="mode === 'edit' ? '编辑活动' : '创建活动'"
    width="600px"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-form-item label="活动名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入活动名称" />
      </el-form-item>

      <el-form-item label="活动类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择活动类型" style="width: 100%">
          <el-option label="会议" value="conference" />
          <el-option label="培训" value="training" />
          <el-option label="活动" value="event" />
          <el-option label="团建" value="team_building" />
        </el-select>
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
          <el-option label="策划中" value="planning" />
          <el-option label="执行中" value="executing" />
          <el-option label="已完成" value="completed" />
          <el-option label="已复盘" value="reviewed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
      </el-form-item>

      <el-form-item label="开始时间" prop="start_date">
        <el-date-picker
          v-model="form.start_date"
          type="datetime"
          placeholder="选择开始时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="预算" prop="budget">
        <el-input-number v-model="form.budget" :min="0" :step="100" style="width: 100%" />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请输入活动描述"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          保存
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useEventsStore } from '@/stores'
import { ElMessage, type FormInstance } from 'element-plus'

interface FormData {
  name: string
  type: string
  status: string
  start_date: string
  budget: number
  description: string
}

const props = defineProps<{
  modelValue: boolean
  eventData?: any
  mode: 'edit' | 'create'
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = ref<FormData>({
  name: '',
  type: 'conference',
  status: 'planning',
  start_date: '',
  budget: 0,
  description: ''
})

const rules = {
  name: [
    { required: true, message: '请输入活动名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在1到200字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择活动类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

watch(() => props.eventData, (newData) => {
  if (newData && props.mode === 'edit') {
    form.value = {
      name: newData.name || '',
      type: newData.type || 'conference',
      status: newData.status || 'planning',
      start_date: newData.start_date || '',
      budget: newData.budget || 0,
      description: newData.description || ''
    }
  } else if (props.mode === 'create') {
    form.value = {
      name: '',
      type: 'conference',
      status: 'planning',
      start_date: '',
      budget: 0,
      description: ''
    }
  }
}, { immediate: true })

const eventsStore = useEventsStore()

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (props.mode === 'edit' && props.eventData?.id) {
        await eventsStore.updateEvent(String(props.eventData.id), form.value)
        ElMessage.success('活动更新成功')
      } else {
        await eventsStore.createEvent(form.value)
        ElMessage.success('活动创建成功')
      }
      emit('success')
      handleClose()
    } catch (error: any) {
      console.error('Save error:', error)
      ElMessage.error(error.message || '操作失败')
    } finally {
      loading.value = false
    }
  })
}

function handleClose() {
  formRef.value?.resetFields()
  isOpen.value = false
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
