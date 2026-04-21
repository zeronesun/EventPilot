<template>
  <div class="kanban-column" :data-status="status">
    <draggable
      v-model="localTasks"
      group="kanban"
      item-key="id"
      :animation="200"
      :disabled="disabled"
      @drag="onDragStart"
      @end="onDragEnd"
      ghost-class="ghost-card"
      drag-class="dragging-card"
    >
      <template #item="{ element: task }">
        <div class="kanban-card" :data-task-id="task.id">
          <slot name="card" :task="task" :click="onCardClick">
            <!-- 默认卡片内容 -->
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <el-tag size="small" :type="getPriorityType(task.priority)">
                {{ getPriorityText(task.priority) }}
              </el-tag>
              <span class="task-assignee">{{ task.assignee_name || task.assignee?.username || '未分配' }}</span>
            </div>
          </slot>
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import draggable from 'vuedraggable/dist/vuedraggable.common.js';

const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  },
  status: {
    type: String,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:tasks', 'dragEnd', 'cardClick']);

// 本地任务列表副本（用于过滤和操作）
const localTasks = ref([...props.tasks]);

watch(() => props.tasks, (newTasks) => {
  localTasks.value = [...newTasks];
}, { deep: true });

const isDragging = ref(false);

function onDragStart() {
  isDragging.value = true;
}

function onDragEnd(event) {
  isDragging.value = false;
  emit('update:tasks', localTasks.value);
  emit('dragEnd', event);
}

function onCardClick(task) {
  emit('cardClick', task);
}

function getPriorityType(priority) {
  const map = {
    low: '',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  };
  return map[priority] || '';
}

function getPriorityText(priority) {
  const map = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  };
  return map[priority] || priority;
}
</script>

<style scoped>
.kanban-column {
  min-height: 120px;
  transition: all 0.3s ease;
}

.kanban-card {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: move;
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275),
              box-shadow 0.2s ease,
              background-color 0.2s ease,
              border-color 0.2s ease;
  border: 1px solid #e4e7ed;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.kanban-card:active {
  transform: scale(1.02);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

.ghost-card {
  opacity: 0.5;
  background: #f5f7fa;
  border: 2px dashed #409eff;
}

.dragging-card {
  opacity: 0.8;
  transform: scale(1.05);
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  word-break: break-word;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-assignee {
  font-size: 12px;
  color: #909399;
}
</style>
