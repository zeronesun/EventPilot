<template>
  <div class="file-manager">
    <!-- 工具栏 -->
    <div class="file-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文件..."
          :prefix-icon="Search"
          @change="handleSearch"
          style="width: 250px"
          clearable
        />
        <el-select
          v-model="filterCategory"
          placeholder="文件分类"
          @change="handleFilter"
          style="width: 150px"
          clearable
        >
          <el-option label="文档" value="document" />
          <el-option label="图片" value="image" />
          <el-option label="视频" value="video" />
          <el-option label="音频" value="audio" />
          <el-option label="压缩包" value="archive" />
          <el-option label="其他" value="other" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" :icon="Upload" @click="handleUpload"> 上传文件 </el-button>
        <el-button
          :icon="Download"
          @click="handleBatchDownload"
          :disabled="selectedFiles.length === 0"
        >
          批量下载
        </el-button>
        <el-button
          type="danger"
          :icon="Delete"
          @click="handleBatchDelete"
          :disabled="selectedFiles.length === 0"
        >
          批量删除
        </el-button>
        <el-dropdown @command="handleSortChange">
          <el-button :icon="Sort">
            排序
            <el-icon class="el-icon--right">
              <ArrowDown />
            </el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="name">按名称</el-dropdown-item>
              <el-dropdown-item command="size">按大小</el-dropdown-item>
              <el-dropdown-item command="date">按日期</el-dropdown-item>
              <el-dropdown-item command="type">按类型</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="32">
          <Loading />
        </el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="files.length === 0" class="empty-container">
        <el-empty description="暂无文件">
          <el-button type="primary" @click="handleUpload">上传文件</el-button>
        </el-empty>
      </div>

      <div v-else>
        <!-- 表格视图 -->
        <el-table
          v-if="viewMode === 'table'"
          :data="files"
          @selection-change="handleSelectionChange"
          style="width: 100%"
          stripe
        >
          <el-table-column type="selection" width="55" />
          <el-table-column label="文件名" min-width="180">
            <template #default="{ row }">
              <div class="file-name-cell">
                <el-icon :size="24" class="file-icon">
                  <component :is="getFileIcon(row.file_type)" />
                </el-icon>
                <span class="file-name">{{ row.original_filename }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="大小" width="100">
            <template #default="{ row }">
              {{ formatFileSize(row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              {{ getFileTypeLabel(row.file_type) }}
            </template>
          </el-table-column>
          <el-table-column label="分类" width="90">
            <template #default="{ row }">
              <el-tag size="small">{{ getCategoryLabel(row.file_category) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="上传时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button :icon="Download" size="small" @click="handleDownload(row)">
                下载
              </el-button>
              <el-button :icon="Share" size="small" @click="handleShare(row)"> 分享 </el-button>
              <el-dropdown @command="(cmd) => handleDropdownCommand(cmd, row)">
                <el-button :icon="More" circle size="small" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="view">查看详情</el-dropdown-item>
                    <el-dropdown-item command="edit">编辑元数据</el-dropdown-item>
                    <el-dropdown-item command="rename">重命名</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>

        <!-- 网格视图 -->
        <div v-else class="grid-view">
          <div
            v-for="file in files"
            :key="file.file_id"
            class="file-card"
            :class="{ selected: isFileSelected(file.file_id) }"
            @click="toggleFileSelection(file.file_id)"
            @contextmenu.prevent="handleContextMenu($event, file)"
          >
            <div class="file-preview">
              <el-icon :size="48" class="preview-icon">
                <component :is="getFileIcon(file.file_type)" />
              </el-icon>
            </div>
            <div class="file-info">
              <div class="file-name" :title="file.original_filename">
                {{ file.original_filename }}
              </div>
              <div class="file-meta">
                {{ formatFileSize(file.file_size) }}
                <span class="separator">•</span>
                {{ getFileTypeLabel(file.file_type) }}
              </div>
              <div class="file-status">
                <el-tag :type="getStatusType(file.status)" size="small">
                  {{ getStatusLabel(file.status) }}
                </el-tag>
              </div>
            </div>
            <div class="file-actions" @click.stop>
              <el-button :icon="Download" size="small" @click="handleDownload(file)" />
              <el-button :icon="Share" size="small" @click="handleShare(file)" />
              <el-dropdown @command="(cmd) => handleDropdownCommand(cmd, file)">
                <el-button :icon="More" size="small" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="view">查看详情</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="total"
        :disabled="loading"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 文件详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="文件详情" width="600px">
      <div v-if="currentFile" class="file-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名">
            {{ currentFile.original_filename }}
          </el-descriptions-item>
          <el-descriptions-item label="文件ID">
            {{ currentFile.file_id }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(currentFile.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="文件类型">
            {{ currentFile.mime_type }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag size="small">{{ getCategoryLabel(currentFile.file_category) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentFile.status)" size="small">
              {{ getStatusLabel(currentFile.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">
            {{ formatDateTime(currentFile.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="可见性">
            <el-tag size="small">{{ getVisibilityLabel(currentFile.visibility) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="2" v-if="currentFile.tags?.length">
            <el-space>
              <el-tag v-for="tag in currentFile.tags" :key="tag" size="small">
                {{ tag }}
              </el-tag>
            </el-space>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2" v-if="currentFile.description">
            {{ currentFile.description }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 分享对话框 -->
    <el-dialog v-model="shareDialogVisible" title="分享文件" width="500px">
      <el-form :model="shareForm" label-width="100px">
        <el-form-item label="分享设置">
          <el-checkbox v-model="shareForm.allow_download">允许下载</el-checkbox>
          <el-checkbox v-model="shareForm.allow_preview">允许预览</el-checkbox>
        </el-form-item>
        <el-form-item label="有效期">
          <el-input-number
            v-model="shareForm.expires_hours"
            :min="1"
            :max="8760"
            :step="24"
            placeholder="小时"
          />
          <span style="margin-left: 8px">小时</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="shareForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选的分享描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shareDialogVisible = false">关闭</el-button>
        <el-button v-if="currentFile?.has_share" type="danger" plain @click="handleRevokeShare">
          取消分享
        </el-button>
        <el-button type="primary" @click="confirmShare">创建分享</el-button>
      </template>
    </el-dialog>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文件" width="600px">
      <FileUploader @upload-success="handleUploadSuccess" @upload-error="handleUploadError" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  Search,
  Upload,
  Download,
  Delete,
  Sort,
  ArrowDown,
  Loading,
  Share,
  More,
  Files,
  Picture,
  VideoPlay,
  Headset,
  Folder,
  Document,
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { filesApi } from '@/api/client';
import type { FileMetadata } from '@/api/client';
import FileUploader from './FileUploader.vue';

const emit = defineEmits(['file-selected', 'file-deleted']);

const files = ref<FileMetadata[]>([]);
const loading = ref(false);
const searchQuery = ref('');
const filterCategory = ref('');
const selectedFiles = ref<string[]>([]);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const viewMode = ref<'table' | 'grid'>('table');

// 对话框
const detailDialogVisible = ref(false);
const shareDialogVisible = ref(false);
const uploadDialogVisible = ref(false);
const currentFile = ref<FileMetadata | null>(null);

// 分享表单
const shareForm = ref({
  allow_download: true,
  allow_preview: true,
  expires_hours: 168, // 默认7天
  description: '',
});

// 加载文件列表
const loadFiles = async () => {
  loading.value = true;
  try {
    const params: Record<string, string> = {
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
    };

    if (searchQuery.value) {
      params['search'] = searchQuery.value;
    }

    if (filterCategory.value) {
      params['category'] = filterCategory.value;
    }

    const response = await filesApi.list(params);
    files.value = response.files;
    total.value = response.total;
  } catch (error) {
    console.error('加载文件列表失败:', error);
    ElMessage.error('加载文件列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadFiles();
};

// 处理过滤
const handleFilter = () => {
  currentPage.value = 1;
  loadFiles();
};

// 处理选择变化
const handleSelectionChange = (selection: FileMetadata[]) => {
  selectedFiles.value = selection.map((f) => f.file_id);
};

// 切换视图模式
const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'table' ? 'grid' : 'table';
};

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

// 格式化日期时间
const formatDateTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// 获取文件图标
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

// 获取分类标签
const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    document: '文档',
    image: '图片',
    video: '视频',
    audio: '音频',
    archive: '压缩包',
    other: '其他',
  };
  return labels[category] || category;
};

// 获取状态标签
const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    uploading: '上传中',
    processing: '处理中',
    completed: '完成',
    failed: '失败',
    deleted: '已删除',
  };
  return labels[status] || status;
};

// 获取状态类型
const getStatusType = (status: string): any => {
  const types: Record<string, any> = {
    uploading: 'warning',
    processing: 'info',
    completed: 'success',
    failed: 'danger',
    deleted: 'info',
  };
  return types[status] || '';
};

// 获取可见性标签
const getVisibilityLabel = (visibility: string): string => {
  const labels: Record<string, string> = {
    private: '私有',
    team: '团队可见',
    public: '公开',
    shared: '已分享',
  };
  return labels[visibility] || visibility;
};

// 获取文件类型标签
const getFileTypeLabel = (type: string): string => {
  if (type?.includes('pdf')) return 'PDF';
  if (type?.includes('word') || type?.includes('doc')) return 'Word';
  if (type?.includes('excel') || type?.includes('xls')) return 'Excel';
  if (type?.includes('PowerPoint') || type?.includes('ppt')) return 'PPT';
  if (type?.includes('image')) return '图片';
  if (type?.includes('video')) return '视频';
  if (type?.includes('audio')) return '音频';
  if (type?.includes('zip') || type?.includes('archive')) return '压缩包';
  return '文件';
};

// 处理上传
const handleUpload = () => {
  uploadDialogVisible.value = true;
};

// 上传成功回调
const handleUploadSuccess = (result: any) => {
  uploadDialogVisible.value = false;
  ElMessage.success('文件上传成功');
  loadFiles();
};

// 上传失败回调
const handleUploadError = (error: string) => {
  ElMessage.error(`上传失败: ${error}`);
};

// 处理下载
const handleDownload = async (file: FileMetadata) => {
  try {
    const response = await filesApi.download(file.file_id);

    // 创建临时下载链接
    const link = document.createElement('a');
    link.href = response.download_url;
    link.download = response.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    ElMessage.success('下载已开始');
  } catch (error) {
    console.error('下载失败:', error);
    ElMessage.error('下载失败');
  }
};

// 批量下载
const handleBatchDownload = async () => {
  try {
    for (const fileId of selectedFiles.value) {
      const file = files.value.find((f) => f.file_id === fileId);
      if (file) {
        await handleDownload(file);
        await new Promise((resolve) => setTimeout(resolve, 500)); // 避免同时下载多个文件
      }
    }
  } catch (error) {
    console.error('批量下载失败:', error);
    ElMessage.error('批量下载失败');
  }
};

// 处理分享
const handleShare = (file: FileMetadata) => {
  currentFile.value = file;
  shareForm.value = {
    allow_download: true,
    allow_preview: true,
    expires_hours: 168,
    description: '',
  };
  shareDialogVisible.value = true;
};

// 确认分享
const confirmShare = async () => {
  if (!currentFile.value) return;

  try {
    const response = await filesApi.share(currentFile.value.file_id, shareForm.value);

    // 复制分享链接到剪贴板
    await navigator.clipboard.writeText(response.share_url);

    // 标记文件已有分享
    currentFile.value.has_share = true;

    shareDialogVisible.value = false;
    ElMessage.success('分享链接已复制到剪贴板');
  } catch (error) {
    console.error('创建分享失败:', error);
    ElMessage.error('创建分享失败');
  }
};

// 取消分享
const handleRevokeShare = async () => {
  if (!currentFile.value) return;

  try {
    await ElMessageBox.confirm(
      '确定要取消该文件的分享链接吗？取消后所有分享链接将失效。',
      '确认取消分享',
      { confirmButtonText: '确定取消', cancelButtonText: '保留', type: 'warning' }
    );

    const response = await filesApi.revokeShare(currentFile.value.file_id);

    // 更新状态
    currentFile.value.has_share = false;
    shareDialogVisible.value = false;
    ElMessage.success(response.message || '已成功取消分享');
  } catch (error: unknown) {
    if (error === 'cancel') return;
    console.error('取消分享失败:', error);
    ElMessage.error('取消分享失败');
  }
};

// 批量删除
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );

    const response = await filesApi.batchDelete(selectedFiles.value);

    if (response.deleted_count > 0) {
      ElMessage.success(`成功删除 ${response.deleted_count} 个文件`);
      selectedFiles.value = [];
      loadFiles();
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error);
      ElMessage.error('批量删除失败');
    }
  }
};

// 处理下拉菜单命令
const handleDropdownCommand = async (cmd: string, file: FileMetadata) => {
  switch (cmd) {
    case 'view':
      currentFile.value = file;
      detailDialogVisible.value = true;
      break;
    case 'delete':
      await handleDeleteFile(file);
      break;
    case 'edit':
      ElMessage.info('编辑功能暂未实现');
      break;
    case 'rename':
      ElMessage.info('重命名功能暂未实现');
      break;
  }
};

// 删除单个文件
const handleDeleteFile = async (file: FileMetadata) => {
  try {
    await ElMessageBox.confirm(`确定要删除文件 "${file.original_filename}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    await filesApi.delete(file.file_id);
    ElMessage.success('文件已删除');
    loadFiles();
    emit('file-deleted', file.file_id);
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error);
      ElMessage.error('删除文件失败');
    }
  }
};

// 处理排序变化
const handleSortChange = (command: string) => {
  ElMessage.info(`按${command}排序功能暂未实现`);
};

// 处理分页大小变化
const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize;
  currentPage.value = 1;
  loadFiles();
};

// 处理页码变化
const handlePageChange = (newPage: number) => {
  currentPage.value = newPage;
  loadFiles();
};

// 检查文件是否被选中
const isFileSelected = (fileId: string): boolean => {
  return selectedFiles.value.includes(fileId);
};

// 切换文件选择
const toggleFileSelection = (fileId: string) => {
  const index = selectedFiles.value.indexOf(fileId);
  if (index > -1) {
    selectedFiles.value.splice(index, 1);
  } else {
    selectedFiles.value.push(fileId);
  }
};

// 处理右键菜单
const handleContextMenu = (event: MouseEvent, file: FileMetadata) => {
  event.preventDefault();
  // 可以在这里实现右键菜单功能
};

// 加载文件列表
onMounted(() => {
  loadFiles();
});
</script>

<style scoped>
.file-manager {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-list {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #909399;
}

.empty-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  flex-shrink: 0;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.file-card {
  position: relative;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.file-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.file-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.file-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  margin-bottom: 12px;
}

.preview-icon {
  color: #409eff;
}

.file-info {
  text-align: center;
}

.file-card .file-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.separator {
  margin: 0 4px;
}

.file-status {
  display: flex;
  justify-content: center;
}

.file-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 4px;
}

.pagination-container {
  padding: 16px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
}

.file-detail {
  padding: 16px 0;
}
</style>
