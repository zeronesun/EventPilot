<template>
  <div class="skeleton" :class="`skeleton--${type}`" :style="containerStyle">
    <div v-if="type === 'text'" class="skeleton-text" :style="textStyle"></div>
    <div v-if="type === 'button'" class="skeleton-button" :style="buttonStyle"></div>
    <div
      v-if="type === 'avatar'"
      class="skeleton-avatar"
      :style="{ width: size, height: size }"
    ></div>
    <div v-if="type === 'card'" class="skeleton-card">
      <div class="skeleton-card__header" :style="cardHeaderStyle"></div>
      <div v-if="showImage" class="skeleton-card__image"></div>
      <div class="skeleton-card__content">
        <div v-for="i in lines" :key="i" class="skeleton-card__line" :style="lineStyle(i)"></div>
      </div>
    </div>
    <div v-if="type === 'list' && Array.isArray(count)" class="skeleton-list">
      <div v-for="i in count" :key="i" class="skeleton-list__item">
        <div v-if="showAvatar" class="skeleton-list__avatar"></div>
        <div class="skeleton-list__content">
          <div class="skeleton-list__title"></div>
          <div v-for="j in lines" :key="j" class="skeleton-list__line"></div>
        </div>
      </div>
    </div>
    <div v-if="type === 'table'" class="skeleton-table">
      <div class="skeleton-table__header">
        <div v-for="col in columns" :key="col" class="skeleton-table__th"></div>
      </div>
      <div class="skeleton-table__body">
        <div v-for="row in rows" :key="row" class="skeleton-table__tr">
          <div v-for="col in columns" :key="col" class="skeleton-table__td"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  type?: 'text' | 'button' | 'avatar' | 'card' | 'list' | 'table';
  width?: string | number;
  height?: string | number;
  size?: string;
  rows?: number;
  columns?: number;
  lines?: number;
  showAvatar?: boolean;
  showImage?: boolean;
  count?: number;
  active?: boolean;
  loading?: boolean;
  customClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  width: '100%',
  height: '20px',
  size: '40px',
  rows: 5,
  columns: 4,
  lines: 3,
  showAvatar: true,
  showImage: false,
  active: true,
  loading: false,
});

const containerStyle = computed(() => ({
  width:
    props.width != null
      ? typeof props.width === 'number'
        ? `${props.width}px`
        : props.width
      : undefined,
  height:
    props.height != null
      ? typeof props.height === 'number'
        ? `${props.height}px`
        : props.height
      : undefined,
}));

const textStyle = computed(() => ({
  width:
    props.width != null
      ? typeof props.width === 'number'
        ? `${props.width}px`
        : props.width
      : undefined,
  height:
    props.height != null
      ? typeof props.height === 'number'
        ? `${props.height}px`
        : props.height
      : undefined,
}));

const buttonStyle = computed(() => ({
  width:
    props.width != null
      ? typeof props.width === 'number'
        ? `${props.width}px`
        : props.width
      : undefined,
  height:
    props.height != null
      ? typeof props.height === 'number'
        ? `${props.height}px`
        : props.height
      : undefined,
}));

const cardHeaderStyle = computed(() => ({
  width: '30%',
  height: '24px',
}));

const lineStyle = (index: number) => {
  const width = index === props.lines ? '60%' : '100%';
  return { width };
};
</script>

<style scoped>
.skeleton {
  display: inline-block;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

/* 骨架屏动画 */
.skeleton::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.4) 50%,
    transparent 100%
  );
  transform: translateX(-100%);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}

.skeleton--text {
  display: inline-block;
  vertical-align: middle;
}

.skeleton--button {
  display: inline-block;
  border-radius: 4px;
}

.skeleton--avatar {
  border-radius: 50%;
  flex-shrink: 0;
}

/* 卡片骨架屏 */
.skeleton-card {
  padding: 20px;
  border-radius: 8px;
  background: #fff;
}

.skeleton-card__header {
  margin-bottom: 16px;
  border-radius: 4px;
  background: #f0f2f5;
}

.skeleton-card__image {
  width: 100%;
  height: 180px;
  background: #f0f2f5;
  border-radius: 8px;
  margin-bottom: 16px;
}

.skeleton-card__content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-card__line {
  height: 16px;
  background: #f0f2f5;
  border-radius: 4px;
}

/* 列表骨架屏 */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-list__item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}

.skeleton-list__avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f2f5;
  flex-shrink: 0;
}

.skeleton-list__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-list__title {
  height: 20px;
  width: 40%;
  background: #f0f2f5;
  border-radius: 4px;
}

.skeleton-list__line {
  height: 14px;
  width: 100%;
  background: #f0f2f5;
  border-radius: 4px;
}

/* 表格骨架屏 */
.skeleton-table {
  width: 100%;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.skeleton-table__header {
  display: flex;
  gap: 10px;
  padding: 16px;
  border-bottom: 1px solid #f0f2f5;
}

.skeleton-table__th {
  height: 20px;
  background: #f0f2f5;
  border-radius: 4px;
  flex: 1;
}

.skeleton-table__body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
}

.skeleton-table__tr {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 4px;
}

.skeleton-table__td {
  height: 16px;
  background: #f0f2f5;
  border-radius: 4px;
  flex: 1;
}

/* 禁止动画的效果 */
.skeleton:not(.skeleton--active)::after {
  animation: none;
}

/* 暗黑模式支持 */
@media (prefers-color-scheme: dark) {
  .skeleton {
    background: #2c2c2c;
  }

  .skeleton::after {
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.1) 50%,
      transparent 100%
    );
  }

  .skeleton-card__header,
  .skeleton-card__image,
  .skeleton-card__line,
  .skeleton-list__avatar,
  .skeleton-list__title,
  .skeleton-list__line,
  .skeleton-table__th,
  .skeleton-table__td {
    background: #3a3a3a;
  }

  .skeleton-card,
  .skeleton-list__item,
  .skeleton-table {
    background: #1a1a1a;
  }

  .skeleton-table__tr {
    background: #2a2a2a;
  }

  .skeleton-card__image,
  .skeleton-list__item,
  .skeleton-table__th {
    border-color: #3a3a3a;
  }
}
</style>
