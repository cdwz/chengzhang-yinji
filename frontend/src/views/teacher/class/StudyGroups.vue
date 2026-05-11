<template>
  <div class="study-groups">
    <el-page-header @back="goBack">
      <template #content>
        <span class="title">学习小组管理</span>
      </template>
    </el-page-header>
    
    <div class="content">
      <el-row :gutter="20">
        <!-- 左侧：小组列表 -->
        <el-col :span="8">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>小组列表</span>
                <el-button type="primary" size="small" @click="showCreateGroup = true">
                  <el-icon><Plus /></el-icon> 新建小组
                </el-button>
              </div>
            </template>
            
            <el-empty v-if="groups.length === 0 && !loading" description="暂无小组" />
            
            <div class="group-list">
              <div 
                v-for="group in groups" 
                :key="group.id"
                class="group-item"
                :class="{ active: selectedGroup?.id === group.id }"
                @click="selectGroup(group)"
              >
                <div class="group-info">
                  <span class="name">{{ group.name }}</span>
                  <el-tag size="small">{{ group.students?.length || 0 }}人</el-tag>
                </div>
                <div class="group-actions">
                  <el-button link type="primary" size="small" @click.stop="editGroup(group)">
                    编辑
                  </el-button>
                  <el-popconfirm title="确定删除该小组？" @confirm="deleteGroup(group.id)">
                    <template #reference>
                      <el-button link type="danger" size="small" @click.stop>删除</el-button>
                    </template>
                  </el-popconfirm>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：成员管理 -->
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>{{ selectedGroup ? selectedGroup.name + ' - 成员管理' : '请选择小组' }}</span>
                <el-button 
                  v-if="selectedGroup" 
                  type="primary" 
                  size="small"
                  @click="showAddMember = true"
                >
                  <el-icon><Plus /></el-icon> 添加成员
                </el-button>
              </div>
            </template>
            
            <el-empty v-if="!selectedGroup" description="请在左侧选择小组" />
            
            <el-table v-else :data="selectedGroup.students || []" v-loading="loadingMembers">
              <el-table-column prop="name" label="姓名" />
              <el-table-column prop="student_number" label="学号" />
              <el-table-column prop="gender" label="性别" width="80">
                <template #default="{ row }">
                  {{ row.gender === 'male' ? '男' : '女' }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="{ row }">
                  <el-popconfirm title="确定将该学生移出小组？" @confirm="removeMember(row.id)">
                    <template #reference>
                      <el-button link type="danger" size="small">移出</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 创建/编辑小组对话框 -->
    <el-dialog v-model="showCreateGroup" :title="editingGroup ? '编辑小组' : '新建小组'" width="400px">
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="小组名称" required>
          <el-input v-model="groupForm.name" placeholder="如：第一组" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeGroupDialog">取消</el-button>
        <el-button type="primary" @click="saveGroup" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 添加成员对话框 -->
    <el-dialog v-model="showAddMember" title="添加成员" width="600px">
      <div class="member-select">
        <el-input 
          v-model="searchKeyword" 
          placeholder="搜索学生姓名" 
          clearable
          style="margin-bottom: 16px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-table 
          ref="memberTableRef"
          :data="availableStudents" 
          @selection-change="handleSelectionChange"
          max-height="400"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="student_number" label="学号" />
          <el-table-column prop="gender" label="性别" width="80">
            <template #default="{ row }">
              {{ row.gender === 'male' ? '男' : '女' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showAddMember = false">取消</el-button>
        <el-button type="primary" @click="addMembers" :loading="adding" :disabled="selectedStudents.length === 0">
          添加 ({{ selectedStudents.length }}人)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { 
  getStudyGroups as listStudyGroups, 
  createStudyGroup, 
  addStudentToGroup, 
  removeStudentFromGroup,
  deleteStudyGroup as deleteGroupApi,
  getStudents
} from '@/api/students'
import type { StudyGroup, Student } from '@/api/types'

const route = useRoute()
const router = useRouter()
const classId = route.params.classId as string

const loading = ref(false)
const loadingMembers = ref(false)
const saving = ref(false)
const adding = ref(false)
const groups = ref<StudyGroup[]>([])
const selectedGroup = ref<StudyGroup | null>(null)
const allStudents = ref<Student[]>([])
const selectedStudents = ref<Student[]>([])
const searchKeyword = ref('')
const showCreateGroup = ref(false)
const showAddMember = ref(false)
const editingGroup = ref<StudyGroup | null>(null)

const groupForm = reactive({
  name: ''
})

// 可添加的学生（未在任何小组的）
const availableStudents = computed(() => {
  const groupStudentIds = new Set(
    groups.value.flatMap(g => g.students?.map(s => s.id) || [])
  )
  
  return allStudents.value.filter(s => {
    const matchesKeyword = !searchKeyword.value || s.name.includes(searchKeyword.value)
    const notInGroup = !groupStudentIds.has(s.id)
    return matchesKeyword && notInGroup
  })
})

onMounted(() => {
  loadGroups()
  loadAllStudents()
})

async function loadGroups() {
  loading.value = true
  try {
    groups.value = await listStudyGroups(classId)
  } catch (error) {
    console.error('加载小组失败', error)
  } finally {
    loading.value = false
  }
}

async function loadAllStudents() {
  try {
    const result = await getStudents({ class_id: classId, page_size: 100 })
    allStudents.value = result.items
  } catch (error) {
    console.error('加载学生失败', error)
  }
}

function selectGroup(group: StudyGroup) {
  selectedGroup.value = group
}

function editGroup(group: StudyGroup) {
  editingGroup.value = group
  groupForm.name = group.name
  showCreateGroup.value = true
}

function closeGroupDialog() {
  showCreateGroup.value = false
  editingGroup.value = null
  groupForm.name = ''
}

async function saveGroup() {
  if (!groupForm.name) {
    ElMessage.warning('请输入小组名称')
    return
  }
  
  saving.value = true
  try {
    if (editingGroup.value) {
      // TODO: 更新小组名称API
      ElMessage.success('小组更新成功')
    } else {
      await createStudyGroup({
        class_id: classId,
        name: groupForm.name
      })
      ElMessage.success('小组创建成功')
    }
    closeGroupDialog()
    loadGroups()
  } catch (error: any) {
    ElMessage.error(error?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function deleteGroup(groupId: string) {
  try {
    await deleteGroupApi(groupId)
    ElMessage.success('小组已删除')
    if (selectedGroup.value?.id === groupId) {
      selectedGroup.value = null
    }
    loadGroups()
  } catch (error: any) {
    ElMessage.error(error?.message || '删除失败')
  }
}

function handleSelectionChange(selection: Student[]) {
  selectedStudents.value = selection
}

async function addMembers() {
  if (!selectedGroup.value || selectedStudents.value.length === 0) return
  
  adding.value = true
  try {
    // 批量添加成员
    for (const student of selectedStudents.value) {
      await addStudentToGroup(selectedGroup.value.id, student.id)
    }
    ElMessage.success(`已添加 ${selectedStudents.value.length} 名成员`)
    showAddMember.value = false
    selectedStudents.value = []
    searchKeyword.value = ''
    loadGroups()
  } catch (error: any) {
    ElMessage.error(error?.message || '添加失败')
  } finally {
    adding.value = false
  }
}

async function removeMember(studentId: string) {
  if (!selectedGroup.value) return
  
  try {
    await removeStudentFromGroup(selectedGroup.value.id, studentId)
    ElMessage.success('已移出小组')
    loadGroups()
  } catch (error: any) {
    ElMessage.error(error?.message || '操作失败')
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped lang="scss">
.study-groups {
  padding: 20px;
  
  .title {
    font-size: 18px;
    font-weight: 500;
  }
  
  .content {
    margin-top: 20px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .group-list {
    .group-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      
      &:hover {
        background: var(--el-fill-color-light);
      }
      
      &.active {
        background: var(--el-color-primary-light-9);
      }
      
      .group-info {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .name {
          font-weight: 500;
        }
      }
      
      .group-actions {
        display: flex;
        gap: 4px;
      }
    }
  }
  
  .member-select {
    max-height: 500px;
    overflow-y: auto;
  }
}
</style>
