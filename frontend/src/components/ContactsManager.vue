<!-- 联系人管理组件 -->
<template>
  <div class="contacts-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>联系人管理</h3>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加联系人
          </el-button>
        </div>
      </template>

      <!-- 搜索和过滤 -->
      <div class="filter-section">
        <el-input v-model="searchQuery" placeholder="搜索联系人..." clearable @input="handleSearch">
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 联系人表格 -->
      <div v-loading="loading" class="contacts-table">
        <el-empty v-if="!loading && contacts.length === 0" description="暂无联系人" />

        <el-table v-else :data="paginatedContacts" stripe border>
          <el-table-column prop="name" label="姓名" width="120">
            <template #default="{ row }">
              <div class="contact-name">
                <el-tag v-if="row.is_primary" type="success" size="small">主要</el-tag>
                {{ row.name }}
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="position" label="职位" width="120" />

          <el-table-column label="联系方式" width="200">
            <template #default="{ row }">
              <div class="contact-info">
                <div v-if="row.email" class="contact-item">
                  <el-icon><Message /></el-icon>
                  {{ row.email }}
                </div>
                <div v-if="row.phone" class="contact-item">
                  <el-icon><Phone /></el-icon>
                  {{ row.phone }}
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '活跃' : '非活跃' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="120">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column prop="notes" label="备注" min-width="150" show-overflow-tooltip />

          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="editContact(row)"> 编辑 </el-button>
              <el-button
                v-if="!row.is_primary"
                type="success"
                size="small"
                @click="setAsPrimary(row)"
              >
                设为主要
              </el-button>
              <el-button type="danger" size="small" @click="deleteContact(row)"> 删除 </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div v-if="contacts.length > pageSize" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="contacts.length"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑联系人对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingContact ? '编辑联系人' : '添加联系人'"
      width="600px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="contactForm" :rules="formRules" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="contactForm.name" placeholder="请输入联系人姓名" />
        </el-form-item>

        <el-form-item label="职位" prop="position">
          <el-input v-model="contactForm.position" placeholder="请输入职位" />
        </el-form-item>

        <el-form-item label="职位其他" prop="position_other">
          <el-input v-model="contactForm.position_other" placeholder="其他职位说明" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="contactForm.email" placeholder="请输入邮箱地址" />
        </el-form-item>

        <el-form-item label="电话" prop="phone">
          <el-input v-model="contactForm.phone" placeholder="请输入电话号码" />
        </el-form-item>

        <el-form-item label="地址" prop="address">
          <el-input v-model="contactForm.address" placeholder="请输入地址" />
        </el-form-item>

        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="contactForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>

        <el-form-item label="是否活跃" prop="is_active">
          <el-switch v-model="contactForm.is_active" />
        </el-form-item>

        <el-form-item v-if="!editingContact || !editingContact.is_primary" label="设为主要联系人">
          <el-switch v-model="contactForm.is_primary" />
          <div class="form-tip">主要联系人会在档案详情中优先显示</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, Message, Phone } from '@element-plus/icons-vue';
import { useProfilesStore } from '@/stores/profiles';
import type { ContactPerson } from '@/lib/profiles-client';

const props = defineProps<{
  profileId: string;
}>();

const profilesStore = useProfilesStore();

// 响应式数据
const loading = ref(true);
const contacts = ref<ContactPerson[]>([]);
const searchQuery = ref('');
const currentPage = ref(1);
const pageSize = ref(10);

// 对话框相关
const showAddDialog = ref(false);
const editingContact = ref<ContactPerson | null>(null);
const formRef = ref();
const contactForm = ref({
  name: '',
  position: '',
  position_other: '',
  email: '',
  phone: '',
  address: '',
  notes: '',
  is_active: true,
  is_primary: false,
});

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入联系人姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }],
};

// 分页后的联系人列表
const paginatedContacts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredContacts.value.slice(start, end);
});

// 过滤后的联系人列表
const filteredContacts = computed(() => {
  if (!searchQuery.value.trim()) {
    return contacts.value;
  }

  const query = searchQuery.value.toLowerCase();
  return contacts.value.filter(
    (contact) =>
      contact.name.toLowerCase().includes(query) ||
      contact.position?.toLowerCase().includes(query) ||
      contact.email?.toLowerCase().includes(query) ||
      contact.phone?.includes(query)
  );
});

// 加载联系人列表
const loadContacts = async () => {
  loading.value = true;
  try {
    const result = await profilesStore.fetchContacts(props.profileId);
    if (result.success) {
      contacts.value = result.data || [];
    } else {
      ElMessage.error(result.error || '加载联系人失败');
    }
  } catch (error) {
    console.error('加载联系人失败:', error);
    ElMessage.error('加载联系人失败');
  } finally {
    loading.value = false;
  }
};

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1; // 搜索时重置到第一页
};

// 分页处理
const handlePageChange = (page: number) => {
  currentPage.value = page;
};

// 编辑联系人
const editContact = (contact: ContactPerson) => {
  editingContact.value = contact;
  contactForm.value = {
    name: contact.name,
    position: contact.position || '',
    position_other: contact.position_other || '',
    email: contact.email || '',
    phone: contact.phone || '',
    address: contact.contact_info?.address || '',
    notes: contact.notes || '',
    is_active: contact.is_active,
    is_primary: contact.is_primary,
  };
  showAddDialog.value = true;
};

// 删除联系人
const deleteContact = (contact: ContactPerson) => {
  ElMessageBox.confirm(`确定要删除联系人 "${contact.name}" 吗？`, '确认删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(async () => {
      try {
        const result = await profilesStore.deleteContact(props.profileId, contact.id);

        if (result.success) {
          ElMessage.success('删除成功');
          await loadContacts();
        } else {
          ElMessage.error(result.error || '删除失败');
        }
      } catch (error) {
        console.error('删除联系人失败:', error);
        ElMessage.error('删除联系人失败');
      }
    })
    .catch(() => {
      // 用户取消删除
    });
};

// 设为主要联系人
const setAsPrimary = (contact: ContactPerson) => {
  ElMessageBox.confirm(`确定要将 "${contact.name}" 设为主要联系人吗？`, '确认设置', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'info',
  })
    .then(async () => {
      try {
        // 先取消当前主要联系人状态
        const primaryContact = contacts.value.find((c) => c.is_primary);
        if (primaryContact) {
          await profilesStore.updateContact(props.profileId, primaryContact.id, {
            is_primary: false,
          });
        }

        // 设置新的主要联系人
        const result = await profilesStore.updateContact(props.profileId, contact.id, {
          is_primary: true,
        });

        if (result.success) {
          ElMessage.success('设置成功');
          await loadContacts();
        } else {
          ElMessage.error(result.error || '设置失败');
        }
      } catch (error) {
        console.error('设置主要联系人失败:', error);
        ElMessage.error('设置主要联系人失败');
      }
    })
    .catch(() => {
      // 用户取消设置
    });
};

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate();

    const contactData = {
      ...contactForm.value,
      contact_info: {
        address: contactForm.value.address,
      },
    };

    if (editingContact.value) {
      // 更新联系人
      const result = await profilesStore.updateContact(
        props.profileId,
        editingContact.value.id,
        contactData
      );

      if (result.success) {
        ElMessage.success('更新成功');
        showAddDialog.value = false;
        await loadContacts();
      } else {
        ElMessage.error(result.error || '更新失败');
      }
    } else {
      // 创建联系人
      const result = await profilesStore.createContact(props.profileId, contactData);

      if (result.success) {
        ElMessage.success('创建成功');
        showAddDialog.value = false;
        await loadContacts();
      } else {
        ElMessage.error(result.error || '创建失败');
      }
    }
  } catch (error) {
    console.error('提交表单失败:', error);
    ElMessage.error('操作失败，请检查输入');
  }
};

// 重置表单
const resetForm = () => {
  editingContact.value = null;
  contactForm.value = {
    name: '',
    position: '',
    position_other: '',
    email: '',
    phone: '',
    address: '',
    notes: '',
    is_active: true,
    is_primary: false,
  };
  formRef.value?.resetFields();
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('zh-CN');
};

// 组件挂载时加载联系人列表
onMounted(() => {
  loadContacts();
});
</script>

<style scoped>
.contacts-manager {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-section {
  margin-bottom: 20px;
}

.contacts-table {
  min-height: 400px;
}

.contact-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.contact-info {
  font-size: 12px;
}

.contact-item {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>
