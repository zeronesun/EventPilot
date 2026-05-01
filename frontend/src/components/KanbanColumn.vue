<template>
  <div
    class="kanban-column"
    :class="{ 'is-dragging': isDragging }"
    :data-status="status"
  >
    <draggable
      v-model="localTasks"
      :group="group"
      :animation="animation"
      :disabled="disabled"
      ghost-class="ghost"
      drag-class="dragging"
      :item-key="itemKey"
      @dragstart="onDragStart"
      @dragend="onDragEnd"
      @change="onChange"
    >
      <template #item="{ element: task }">
        <div class="draggable-card">
          <slot
            name="card"
            :task="task"
            :click="onCardClick"
          >
            <div
              class="default-card"
              @click="onCardClick(task)"
            >
              {{ task }}
            </div>
          </slot>
        </div>
      </template>
    </draggable>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import draggable from 'vuedraggable';

const props = defineProps({
  tasks: {
    type: Array,
    default: () => [],
    required: true,
  },
  status: {
    type: String,
    required: true,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  group: {
    type: [String, Object],
    default: 'kanban',
  },
  animation: {
    type: Number,
    default: 200,
  },
  itemKey: {
    type: String,
    default: 'id',
  },
});

const emit = defineEmits(['dragEnd', 'change', 'cardClick', 'dragStart']);

const isDragging = ref(false);

const localTasks = computed({
  get: () => props.tasks,
  set: (value) => {
    emit('change', value);
  },
});

function itemKey(task) {
  return typeof props.itemKey === 'function' ? props.itemKey(task) : task[props.itemKey];
}

function onDragStart(event) {
  isDragging.value = true;
  emit('dragStart', event);
}

function onDragEnd(event) {
  isDragging.value = false;
  emit('dragEnd', event);
}

function onChange(event) {
  emit('change', event);
}

function onCardClick(task) {
  emit('cardClick', task);
}
</script>

<style scoped>
.kanban-column {
  min-height: 80px;
  transition: background-color 0.2s;
}

.kanban-column.is-dragging {
  background-color: var(--el-bg-color-page, #f5f7fa);
  border-radius: 4px;
}

.draggable-card {
  cursor: grab;
  transition:
    transform 0.2s,
    box-shadow 0.2s;
}

.draggable-card:active {
  cursor: grabbing;
}

.ghost {
  opacity: 0.4;
  background: var(--el-color-primary-light-9, #ecf5ff);
  border: 2px dashed var(--el-color-primary-light-7, #b3d8ff);
}

.dragging {
  opacity: 1;
  background: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: rotate(1.5deg) scale(1.02);
  z-index: 1000;
}

.default-card {
  padding: 12px;
  background: var(--el-fill-color-light, #f5f7fa);
  border-radius: 4px;
}
</style>
