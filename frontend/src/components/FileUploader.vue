<template>
  <div class="file-uploader-wrapper">
    <!-- 拖拽上传区域 -->
    <div
      class="upload-dropzone"
      :class="{
        'is-dragover': isDragOver,
        'is-uploading': isUploading,
        'has-error': uploadError,
      }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="upload-content">
        <el-icon class="upload-icon" :size="48">
          <UploadFilled />
        </el-icon>
        <div class="upload-text">
          <p class="upload-title">点击或拖拽文件到此处上传</p>
          <p class="upload-hint">支持文档、图片、视频等，单个文件最大500MB</p>
        </div>
        <el-button type="primary" :icon="Upload">选择文件</el-button>
      </div>
      <input
        ref="fileInputRef"
        type="file"
        :multiple="allowMultiple"
        :accept="acceptedTypes"
        @change="handleFileSelect"
        style="display: none"
      />
    </div>

    <!-- 传递的文件信息（待确认状态） -->
    <div v-if="file && !isUploading && !uploadSuccess" class="file-info-pending" @click.stop>
      <div class="file-thumbnail">
        <el-icon :size="32">
          <component :is="getFileIcon(file.type)" />
        </el-icon>
      </div>
      <div class="file-details">
        <div class="file-name">{{ file.name }}</div>
        <div class="file-meta">
          <span>{{ formatFileSize(file.size) }}</span>
          <span>{{ file.type || '未知类型' }}</span>
        </div>
      </div>
      <div class="pending-actions">
        <el-button type="primary" size="small" :icon="Upload" @click="confirmUpload">确认上传</el-button>
        <el-button size="small" :icon="Delete" @click="removeFile">取消</el-button>
      </div>
    </div>

    <!-- 上传中/已完成时显示的文件信息 -->
    <div v-if="(isUploading || uploadSuccess) && file" class="file-info" @click.stop>
      <div class="file-thumbnail">
        <el-icon :size="32">
          <component :is="getFileIcon(file.type)" />
        </el-icon>
      </div>
      <div class="file-details">
        <div class="file-name">{{ file.name }}</div>
        <div class="file-meta">
          <span>{{ formatFileSize(file.size) }}</span>
          <span>{{ file.type || '未知类型' }}</span>
        </div>
      </div>
      <el-button v-if="!isUploading && !uploadError" type="danger" :icon="Delete" circle size="small" @click="removeFile" />
    </div>

    <!-- 上传进度 -->
    <div v-if="uploadProgress > 0" class="upload-progress" @click.stop>
      <el-progress :percentage="uploadProgress" :status="uploadStatus" :stroke-width="6">
        <template #default="{ percentage }">
          <span class="progress-text">{{ percentage }}%</span>
        </template>
      </el-progress>
      <div class="progress-details">
        <span>{{ uploadSpeed ? `${uploadSpeed}` : '上传中...' }}</span>
        <span>{{ formatTimeRemaining(timeRemaining) }}</span>
      </div>
    </div>

    <!-- 上传结果 -->
    <div v-if="uploadError" class="upload-error" @click.stop>
      <el-alert type="error" :closable="false" show-icon>
        {{ uploadError }}
      </el-alert>
    </div>

    <!-- 上传成功 -->
    <div v-if="uploadSuccess" class="upload-success" @click.stop>
      <el-alert type="success" :closable="false" show-icon> 文件上传成功！ </el-alert>
    </div>

    <!-- 批量上传队列（待确认状态） -->
    <div v-if="queue.length > 0 && !isUploading" class="upload-queue pending-queue" @click.stop>
      <div class="queue-header">
        <span>待上传文件 ({{ queue.length }})</span>
        <div class="queue-header-actions">
          <el-button type="primary" size="small" :icon="Upload" @click="confirmQueueUpload">确认全部上传</el-button>
          <el-button type="danger" text size="small" @click="clearQueue"> 清空队列 </el-button>
        </div>
      </div>
      <div class="queue-items">
        <div v-for="(item, index) in queue" :key="index" class="queue-item queue-item-pending">
          <div class="queue-item-info">
            <el-icon :size="20">
              <component :is="getFileIcon(item.file.type)" />
            </el-icon>
            <div class="queue-item-details">
              <div class="queue-item-name">{{ item.file.name }}</div>
              <div class="queue-item-meta">{{ formatFileSize(item.file.size) }}</div>
            </div>
          </div>
          <el-tag type="info" size="small">等待确认</el-tag>
          <el-button type="danger" text size="small" @click="removeFromQueue(index)">移除</el-button>
        </div>
      </div>
    </div>

    <!-- 批量上传队列（上传中/已完成） -->
    <div v-if="uploadingQueue.length > 0 || (queue.length > 0 && isUploading)" class="upload-queue" @click.stop>
      <div class="queue-header">
        <span>上传队列 ({{ queue.length }})</span>
        <el-button type="danger" text size="small" @click="clearQueue"> 清空队列 </el-button>
      </div>
      <div class="queue-items">
        <div v-for="(item, index) in queue" :key="index" class="queue-item">
          <div class="queue-item-info">
            <el-icon :size="20">
              <component :is="getFileIcon(item.file.type)" />
            </el-icon>
            <div class="queue-item-details">
              <div class="queue-item-name">{{ item.file.name }}</div>
              <div class="queue-item-meta">{{ formatFileSize(item.file.size) }}</div>
            </div>
          </div>
          <div class="queue-item-progress">
            <el-progress :percentage="item.progress" :status="item.status" :stroke-width="4" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import {
  UploadFilled,
  Upload,
  Delete,
  Files,
  Picture,
  VideoPlay,
  Headset,
  Folder,
} from '@element-plus/icons-vue';
import { filesApi, apiClient } from '@/api/client';
import type { FileUploadInitiateResponse } from '@/api/client';

interface FileUploadItem {
  file: File;
  progress: number;
  status: 'uploading' | 'completed' | 'failed';
  fileId?: string;
  uploadId?: string;
  uploadStrategy?: 'direct' | 'multipart';
  error?: string;
}

const props = defineProps({
  modelValue: {
    type: Object as any,
    default: null,
  },
  allowMultiple: {
    type: Boolean,
    default: false,
  },
  acceptedTypes: {
    type: String,
    default: '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.mp4,.mp3',
  },
  maxSize: {
    type: Number,
    default: 500 * 1024 * 1024, // 500MB
  },
});

const emit = defineEmits(['update:modelValue', 'upload-success', 'upload-error']);

const isDragOver = ref(false);
const isUploading = ref(false);
const uploadProgress = ref(0);
const uploadStatus = ref<'success' | 'exception' | undefined>(undefined);
const uploadError = ref('');
const uploadSuccess = ref(false);
const uploadSpeed = ref('');
const timeRemaining = ref(0);

const fileInputRef = ref<HTMLInputElement>();
const file = ref<File | null>(null);
const queue = ref<FileUploadItem[]>([]);
const uploadingQueue = ref<FileUploadItem[]>([]);

const CHUNK_SIZE = 8 * 1024 * 1024; // 8MB
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

const handleDragOver = (e: DragEvent) => {
  isDragOver.value = true;
};

const handleDragLeave = (e: DragEvent) => {
  isDragOver.value = false;
};

const handleDrop = (e: DragEvent) => {
  isDragOver.value = false;
  const droppedFiles = e.dataTransfer?.files;
  if (droppedFiles && droppedFiles.length > 0) {
    if (props.allowMultiple) {
      addFilesToQueue(Array.from(droppedFiles));
    } else {
      selectFile(droppedFiles[0]);
    }
  }
};

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const selectedFiles = target.files;
  if (selectedFiles && selectedFiles.length > 0) {
    if (props.allowMultiple) {
      addFilesToQueue(Array.from(selectedFiles));
    } else {
      selectFile(selectedFiles[0]);
    }
  }
  // 重置input以允许再次选择相同文件
  target.value = '';
};

// 选择文件后暂存，等待用户确认（单文件模式）
const selectFile = (selectedFile: File) => {
  if (!validateFile(selectedFile)) return;
  // 重置状态
  uploadProgress.value = 0;
  uploadStatus.value = undefined;
  uploadError.value = '';
  uploadSuccess.value = false;
  // 暂存文件，不自动上传
  file.value = selectedFile;
};

// 确认上传（单文件）
const confirmUpload = async () => {
  if (!file.value) return;
  await startUpload(file.value);
};

// 添加文件到队列，等待确认（批量模式）
const addFilesToQueue = (files: File[]) => {
  files.forEach((f) => {
    if (validateFile(f)) {
      queue.value.push({
        file: f,
        progress: 0,
        status: 'uploading',
      });
    }
  });
  // 不再自动调用 processQueue，等待用户确认
};

// 确认批量上传
const confirmQueueUpload = async () => {
  if (queue.value.length === 0 || isUploading.value) return;
  await processQueue();
};

// 从队列中移除单个文件
const removeFromQueue = (index: number) => {
  queue.value.splice(index, 1);
};

const validateFile = (file: File): boolean => {
  // 检查文件大小
  if (file.size > props.maxSize) {
    uploadError.value = `文件大小超过限制 (${formatFileSize(props.maxSize)})`;
    return false;
  }

  // 检查文件类型
  if (file.type && !isAcceptedType(file.type)) {
    uploadError.value = `不支持的文件类型: ${file.type}`;
    return false;
  }

  uploadError.value = '';
  return true;
};

const isAcceptedType = (type: string): boolean => {
  if (!type) return true;
  const acceptedTypes = props.acceptedTypes.split(',').map((t) => t.trim());
  return acceptedTypes.some((accept) => type.includes(accept.replace('.', '')));
};

const removeFile = () => {
  file.value = null;
  uploadProgress.value = 0;
  uploadError.value = '';
  uploadSuccess.value = false;
  uploadStatus.value = undefined;
};

const startUpload = async (fileToUpload: File) => {
  isUploading.value = true;
  uploadProgress.value = 0;
  uploadStatus.value = undefined;
  uploadError.value = '';
  uploadSuccess.value = false;

  try {
    // 直接上传文件
    const result = await filesApi.upload(
      fileToUpload,
      (progress) => {
        uploadProgress.value = progress;
      }
    );

    uploadSuccess.value = true;
    uploadStatus.value = 'success';
    emit('upload-success', { file_id: result.file_id, filename: fileToUpload.name });
  } catch (err) {
    const error = err as Error;
    uploadError.value = error.message || '上传失败';
    uploadStatus.value = 'exception';
    emit('upload-error', error.message);
  } finally {
    isUploading.value = false;
  }
};

const processQueue = async () => {
  if (isUploading.value || queue.value.length === 0) return;

  const currentItem = queue.value[0];
  isUploading.value = true;
  // 移到上传中队列
  uploadingQueue.value.push(currentItem);

  try {
    await startUpload(currentItem.file);
    currentItem.progress = 100;
    currentItem.status = 'completed';
  } catch (error) {
    const err = error as Error;
    currentItem.status = 'failed';
    currentItem.error = err.message;
  }

  // 从待确认队列移除
  const idx = queue.value.indexOf(currentItem);
  if (idx > -1) {
    queue.value.splice(idx, 1);
  }
  isUploading.value = false;

  // 继续处理队列中的下一个文件
  if (queue.value.length > 0) {
    processQueue();
  } else {
    // 全部完成，清空上传中队列
    setTimeout(() => {
      uploadingQueue.value = [];
    }, 2000);
  }
};

const clearQueue = () => {
  if (isUploading.value) return;
  queue.value = [];
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

const formatTimeRemaining = (seconds: number): string => {
  if (seconds <= 0) return '计算中...';
  if (seconds < 60) return `${Math.round(seconds)}秒`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`;
  return `${Math.round(seconds / 3600)}小时`;
};

const getFileIcon = (type: string) => {
  if (type?.startsWith('image/')) return Picture;
  if (type?.startsWith('video/')) return VideoPlay;
  if (type?.startsWith('audio/')) return Headset;
  if (
    type?.includes('pdf') ||
    type?.includes('word') ||
    type?.includes('excel') ||
    type?.includes('text')
  )
    return Files;
  return Folder;
};
</script>

<style scoped>
.file-uploader-wrapper {
  width: 100%;
}

.upload-dropzone {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f5f7fa;
}

.upload-dropzone:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-dropzone.is-dragover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: scale(1.02);
}

.upload-dropzone.is-uploading {
  pointer-events: none;
  opacity: 0.7;
}

.upload-dropzone.has-error {
  border-color: #f56c6c;
  background: #fef0f0;
}

.upload-icon {
  color: #409eff;
  margin-bottom: 16px;
}

.upload-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 8px;
}

.upload-hint {
  font-size: 13px;
  color: #909399;
  margin: 0 0 20px;
}

.file-info {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-top: 16px;
}

.file-info-pending {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #ecf5ff 0%, #f0f9ff 100%);
  border: 1px solid #b3d8ff;
  border-radius: 8px;
  margin-top: 16px;
}

.pending-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.file-thumbnail {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background: #fff;
  border-radius: 6px;
  color: #409eff;
  margin-right: 12px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: #909399;
}

.file-meta span {
  margin-right: 8px;
}

.upload-progress {
  margin-top: 16px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #409eff;
}

.progress-details {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.upload-error {
  margin-top: 16px;
}

.upload-success {
  margin-top: 16px;
}

.upload-queue {
  margin-top: 16px;
}

.pending-queue {
  border: 1px solid #b3d8ff;
  background: linear-gradient(180deg, #ecf5ff 0%, #fff 100%);
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px 8px 0 0;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.queue-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.queue-items {
  max-height: 200px;
  overflow-y: auto;
  background: #fff;
  border-radius: 0 0 8px 8px;
  border: 1px solid #ebeef5;
}

.queue-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #f5f7fa;
}

.queue-item:last-child {
  border-bottom: none;
}

.queue-item-pending {
  background: rgba(64, 158, 255, 0.03);
}

.queue-item-pending:hover {
  background: rgba(64, 158, 255, 0.08);
}

.queue-item-info {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.queue-item-details {
  margin-left: 10px;
}

.queue-item-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.queue-item-meta {
  font-size: 11px;
  color: #909399;
}

.queue-item-progress {
  flex: 1;
  margin-left: 15px;
}
</style>
