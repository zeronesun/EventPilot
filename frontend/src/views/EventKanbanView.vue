<template>
  <div class="events-kanban-wrapper">
    <EventsKanban
      @update:statistics="handleStatisticsUpdate"
      @open-details="handleOpenEventDetails"
    />
  </div>
</template>

<script setup>
import EventsKanban from './EventsKanban.vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores'

const router = useRouter()
const eventsStore = useEventsStore()

function handleStatisticsUpdate(eventId, stats) {
  // 更新统计数据到 store
  console.log('Statistics updated:', eventId, stats)
}

function handleOpenEventDetails(event) {
  // 跳转到活动详情页
  if (event?.id) {
    router.push(`/events/${event.id}`)
  }
}
</script>

<style scoped>
.events-kanban-wrapper {
  width: 100%;
  height: 100%;
}
</style>
