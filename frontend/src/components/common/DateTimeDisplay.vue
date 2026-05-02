<template>
  <span class="date-time-display">
    {{ formattedDateTime }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  value: string | Date | null | undefined
  format?: 'full' | 'date' | 'time' | 'short'
  showEmpty?: string
}>()

const formatMap = {
  full: 'YYYY-MM-DD HH:mm:ss',
  date: 'YYYY-MM-DD',
  time: 'HH:mm:ss',
  short: 'MM-DD HH:mm'
}

const formattedDateTime = computed(() => {
  if (!props.value) {
    return props.showEmpty || '未设置'
  }

  try {
    const date = new Date(props.value)
    if (isNaN(date.getTime())) {
      return props.showEmpty || '无效日期'
    }

    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    switch (props.format || 'full') {
      case 'date':
        return `${year}-${month}-${day}`
      case 'time':
        return `${hours}:${minutes}:${seconds}`
      case 'short':
        return `${month}-${day} ${hours}:${minutes}`
      case 'full':
      default:
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    }
  } catch (error) {
    console.error('Date formatting error:', error)
    return props.showEmpty || '日期错误'
  }
})
</script>

<style scoped>
.date-time-display {
  white-space: nowrap;
}
</style>
