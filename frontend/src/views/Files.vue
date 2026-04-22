<template>
  <div class="files-container">
    <div class="page-header">
      <h1>文件管理</h1>
      <el-button type="primary" @click="showUploadDialog">
        上传文件
      </el-button>
    </div>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card class="toolbar-card">
          <el-row :gutter="20" align="middle">
            <el-col :span="12">
              <el-input
                v-model="searchQuery"
                placeholder="搜索文件..."
                clearable
                @input="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-col>
            <el-col :span="8">
              <el-select
                v-model="filterType"
                placeholder="文件类型"
                clearable
                style="width: 100%"
                @change="handleSearch"
              >
                <el-option label="全部类型" value="" />
                <el-option label="图片" value="image" />
                <el-option label="文档" value="document" />
                <el-option label="视频" value="video" />
                <el-option label="音频" value="audio" />
                <el-option label="压缩包" value="archive" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select
                v-model="sortBy"
                placeholder="排序方式"
                @change="handleSearch"
              >
                <el-option label="按名称" value="name" />
                <el-option label="按大小" value="size" />
                <el-option label="按时间" value="time" />
              </el-select>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card class="files-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <h3>我的文件 ({{ filteredFiles.length }})</h3>
                <span class="storage-used">已用 {{ formatBytes(totalSize) }} / {{ formatBytes(quota) }}</span>
              </div>
              <div class="header-right">
                <el-button @click="viewMode = 'grid'" :type="viewMode === 'grid' ? 'primary' : 'default'" circle>
                  <el-icon><Grid /></el-icon>
                </el-button>
                <el-button @click="viewMode = 'list'" :type="viewMode === 'list' ? 'primary' : 'default'" circle>
                  <el-icon><List /></el-icon>
                </el-button>
              </div>
            </div>
          </template>

          <!-- 网格视图 -->
          <div v-if="viewMode === 'grid'" class="grid-view" v-loading="loading">
            <div
              v-for="file in filteredFiles"
              :key="file.id"
              class="file-grid-item"
              @click="handleFileClick(file)"
            >
              <div class="file-thumbnail">
                <img v-if="file.thumbnail_url" :src="file.thumbnail_url" :alt="file.name" />
                <div v-else class="file-icon" :class="getFileIconClass(file.file_type)">
                  <el-icon :size="48"><component :is="getFileIconComponent(file.file_type)" /></el-icon>
                </div>
              </div>
              <div class="file-info">
                <div class="file-name" :title="file.name">{{ file.name }}</div>
                <div class="file-meta">
                  <span class="file-size">{{ formatBytes(file.size) }}</span>
                  <span class="file-type">{{ getFileTypeText(file.file_type) }}</span>
                </div>
                <div class="file-actions">
                  <el-button link type="primary" size="small" @click.stop="handlePreview(file)">
                    预览
                  </el-button>
                  <el-button link type="success" size="small" @click.stop="handleDownload(file)">
                    下载
                  </el-button>
                  <el-button link type="danger" size="small" @click.stop="handleDelete(file)">
                    删除
                  </el-button>
                  <el-dropdown @command="handleMoreAction" @click.stop>
                    <el-button link type="info" size="small">
                      更多<el-icon><ArrowDown /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="() => handleShare(file)">
                          <el-icon><Share /></el-icon>
                          分享
                        </el-dropdown-item>
                        <el-dropdown-item :command="() => handleRename(file)">
                          <el-icon><Edit /></el-icon>
                          重命名
                        </el-dropdown-item>
                        <el-dropdown-item :command="() => handleViewHistory(file)">
                          <el-icon><Clock /></el-icon>
                          版本历史
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </div>
          </div>

          <!-- 列表视图 -->
          <el-table
            v-else
            :data="filteredFiles"
            v-loading="loading"
            stripe
            border
          >
            <el-table-column prop="name" label="文件名" min-width="200">
              <template #default="{ row }">
                <div class="table-file-name">
                  <el-icon :class="getFileIconClass(row.file_type)">
                    <component :is="getFileIconComponent(row.file_type)" />
                  </el-icon>
                  {{ row.name }}
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="file_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="getTypeTagType(row.file_type)">
                  {{ getFileTypeText(row.file_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="size" label="大小" width="100">
              <template #default="{ row }">
                {{ formatBytes(row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handlePreview(row)">
                  预览
                </el-button>
                <el-button link type="success" size="small" @click="handleDownload(row)">
                  下载
                </el-button>
                <el-dropdown @command="handleMoreAction">
                  <el-button link type="info" size="small">
                    更多<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="() => handleShare(row)">
                        <el-icon><Share /></el-icon>
                        分享
                      </el-dropdown-item>
                      <el-dropdown-item :command="() => handleRename(row)">
                        <el-icon><Edit /></el-icon>
                        重命名
                      </el-dropdown-item>
                      <el-dropdown-item :command="() => handleDelete(row)">
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传文件"
      width="700px"
      :close-on-click-modal="false"
    >
      <FileUploader @upload-success="handleUploadSuccess" @upload-error="handleUploadError" />
    </el-dialog>

    <!-- 文件预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="文件预览"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="preview-container" v-loading="previewLoading">
        <div v-if="previewFile && previewFile.file_type.startsWith('image')">
          <img :src="previewFile.url" :alt="previewFile.name" class="preview-image" />
        </div>
        <div v-else class="no-preview">
          <el-empty description="此文件类型暂不支持预览">
            <el-button type="primary" @click="handleDownload(previewFile)">下载文件</el-button>
          </el-empty>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Grid,
  List,
  ArrowDown,
  Share,
  Edit,
  Delete,
  Clock,
  Download,
  Document,
  Picture,
  VideoPlay,
  Microphone,
  FolderOpened
} from '@element-plus/icons-vue'
import FileUploader from '../components/FileUploader.vue'

const loading = ref(false)
const viewMode = ref('grid')
const uploadDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const searchQuery = ref('')
const filterType = ref('')
const sortBy = ref('time')
const previewFile = ref(null)
const quota = 5368709120 // 5GB quota

// 模拟数据 - 实际应该从API获取
const files = ref([
  {
    id: '1',
    name: '活动布置方案.pdf',
    file_type: 'application/pdf',
    size: 2048576,
    created_at: '2026-04-20T10:00:00Z',
    thumbnail_url: '',
    url: 'https://example.com/files/activity-plan.pdf',
    version: 1
  },
  {
    id: '2',
    name: '场地照片1.jpg',
    file_type: 'image/jpeg',
    size: 524288,
    created_at: '2026-04-20T11:30:00Z',
    thumbnail_url: 'https://example.com/thumbs/venue1.jpg',
    url: 'https://example.com/files/venue1.jpg',
    version: 1
  },
  {
    id: '3',
    name: '会议记录.docx',
    file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    size: 1048576,
    created_at: '2026-04-20T14:00:00Z',
    thumbnail_url: '',
    url: 'https://example.com/files/meeting-notes.docx',
    version: 1
  }
])

const filteredFiles = computed(() => {
  let result = [...files.value]
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(f => 
      f.name.toLowerCase().includes(query)
    )
  }
  
  // 类型过滤
  if (filterType.value) {
    result = result.filter(f => 
      f.file_type.includes(filterType.value)
    )
  }
  
  // 排序
  if (sortBy.value === 'name') {
    result.sort((a, b) => a.name.localeCompare(b.name))
  } else if (sortBy.value === 'size') {
    result.sort((a, b) => a.size - b.size)
  } else {
    result.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }
  
  return result
})

const totalSize = computed(() => files.value.reduce((sum, file) => sum + file.size, 0))

function handleSearch() {
  // 搜索和过滤由computed处理
}

function getFileIconClass(fileType) {
  if (fileType.startsWith('image/')) return 'file-icon-image'
  if (fileType.includes('pdf')) return 'file-icon-pdf'
  if (fileType.includes('word') || fileType.includes('document')) return 'file-icon-document'
  if (fileType.includes('video')) return 'file-icon-video'
  if (fileType.includes('audio')) return 'file-icon-audio'
  if (fileType.includes('zip') || fileType.includes('archive')) return 'file-icon-archive'
  return 'file-icon-other'
}

function getFileIconComponent(fileType) {
  if (fileType.startsWith('image/')) return Picture
  if (fileType.includes('pdf')) return Document
  if (fileType.includes('video')) return VideoPlay
  if (fileType.includes('audio')) return Microphone
  return Document
}

function getFileTypeText(fileType) {
  if (fileType.startsWith('image/')) return '图片'
  if (fileType.includes('pdf')) return 'PDF文档'
  if (fileType.includes('word') || fileType.includes('document')) return '文档'
  if (fileType.includes('video')) return '视频'
  if (fileType.includes('audio')) return '音频'
  if (fileType.includes('zip') || fileType.includes('archive')) return '压缩包'
  return '其他'
}

function getTypeTagType(fileType) {
  if (fileType.startsWith('image/')) return 'success'
  if (fileType.includes('pdf')) return 'warning'
  if (fileType.includes('video')) return 'danger'
  if (fileType.includes('audio')) return 'info'
  return 'info'
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

function showUploadDialog() {
  uploadDialogVisible.value = true
}

function handleFileClick(file) {
  previewFile.value = file
  previewDialogVisible.value = true
}

function handlePreview(file) {
  previewFile.value = file
  previewDialogVisible.value = true
}

async function handleDownload(file) {
  try {
    ElMessage.success('开始下载文件...')
    // TODO: 实现文件下载逻辑
    window.open(file.url, '_blank')
  } catch (error) {
    console.error('Download failed:', error)
    ElMessage.error('下载失败')
  }
}

function handleShare(file) {
  ElMessage.info(`分享文件: ${file.name}`)
}

function handleRename(file) {
  ElMessage.info(`重命名: ${file.name}`)
}

function handleViewHistory(file) {
  ElMessage.info(`版本历史: ${file.name}`)
}

function handleMoreAction(action) {
  // 处理更多操作
  console.log('More action:', action)
}

function handleUploadSuccess(result) {
  ElMessage.success('文件上传成功')
  uploadDialogVisible.value = false
  //刷新文件列表
}

function handleUploadError(error) {
  ElMessage.error(`上传失败: ${error.message}`)
}

onMounted(() => {
  // TODO: 从API加载文件列表
})
</script>

<style scoped>
.files-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.toolbar-card {
  background: #fff;
}

.files-card {
  min-height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.storage-used {
  font-size: 13px;
  color: #666;
}

.header-right {
  display: flex;
  gap: 10px;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.file-grid-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.file-grid-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.file-thumbnail {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  overflow: hidden;
}

.file-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.file-icon {
  font-size: 48px;
  color: #999;
}

.file-icon-image {
  color: #67C23A;
}

.file-icon-pdf {
  color: #F56C6C;
}

.file-icon-video {
  color: #409EFF;
}

.file-icon-audio {
  color: #909399;
}

.file-icon-archive {
  color: #E6A23C;
}

.file-icon-other {
  color: #909399;
}

.file-info {
  padding: 15px;
}

.file-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: #666;
  display: flex;
  gap: 10px;
}

.file-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.table-file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-image {
  width: 100%;
  height: auto;
  max-height: 600px;
  object-fit: contain;
}

.preview-container {
  min-height: 300px;
}

.no-preview {
  text-align: center;
  padding: 40px 0;
}
</style>