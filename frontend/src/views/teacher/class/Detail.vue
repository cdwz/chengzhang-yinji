<template>
  <div class="class-detail">
    <!-- 班级信息卡片 -->
    <van-cell-group inset class="info-card">
      <van-cell title="班级名称" :value="classInfo?.name" />
      <van-cell title="所属年级" :value="classInfo?.grade?.name" />
      <van-cell title="学生人数" :value="classInfo?.student_count?.toString() || '0'" />
      <van-cell title="邀请码" :value="classInfo?.invite_code">
        <template #right-icon>
          <van-icon name="description" @click="copyInviteCode" />
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 标签页切换 -->
    <van-tabs v-model:active="activeTab" sticky>
      <!-- 学生列表 -->
      <van-tab title="学生列表" name="students">
        <div class="tab-content">
          <div class="action-bar">
            <van-button type="primary" size="small" @click="showImportDialog = true">
              导入学生
            </van-button>
            <van-button size="small" @click="loadStudents">刷新</van-button>
          </div>

          <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
            <van-list
              v-model:loading="loading"
              :finished="finished"
              finished-text="没有更多了"
              @load="loadStudents"
            >
              <van-cell
                v-for="student in students"
                :key="student.id"
                :title="student.name"
                :label="`学号: ${student.student_number || '未设置'}${student.status && student.status !== 'active' ? ' · ' + statusName(student.status) : ''}`"
              >
                <template #icon>
                  <van-icon
                    :name="student.gender === 'female' ? 'contact' : 'contact'"
                    :color="student.gender === 'female' ? '#ff69b4' : '#1890ff'"
                    size="24"
                    style="margin-right: 8px;"
                  />
                </template>
                <template #value>
                  <div class="student-actions">
                    <van-tag v-if="student.study_group_id" type="primary" style="margin-right:4px">
                      {{ getGroupName(student.study_group_id) }}
                    </van-tag>
                    <van-icon name="edit" size="18" color="#3e7dc9" @click.stop="openEditStudent(student)" />
                    <van-icon name="delete-o" size="18" color="#ee0a24" style="margin-left:8px" @click.stop="confirmDeleteStudent(student)" />
                  </div>
                </template>
              </van-cell>
            </van-list>
          </van-pull-refresh>
        </div>
      </van-tab>

      <!-- 学习小组 -->
      <van-tab title="学习小组" name="groups">
        <div class="tab-content">
          <div class="action-bar">
            <van-button type="primary" size="small" @click="showCreateGroup = true">
              创建小组
            </van-button>
            <van-button size="small" @click="loadGroups">刷新</van-button>
          </div>

          <van-collapse v-model="activeGroups">
            <van-collapse-item
              v-for="group in groups"
              :key="group.id"
              :name="group.id"
            >
              <template #title>
                <div class="group-title">
                  <span>{{ group.name }}</span>
                  <van-tag type="primary">{{ group.students?.length || 0 }}人</van-tag>
                </div>
              </template>
              
              <van-cell-group>
                <van-cell
                  v-for="student in group.students"
                  :key="student.id"
                  :title="student.name"
                >
                  <template #right-icon>
                    <van-icon name="cross" @click.stop="removeFromGroup(group.id, student.id)" />
                  </template>
                </van-cell>
                <van-cell
                  v-if="!group.students?.length"
                  title="暂无成员"
                  title-style="color: #999;"
                />
              </van-cell-group>
            </van-collapse-item>
          </van-collapse>

          <van-empty v-if="!groups.length" description="暂无学习小组" />
        </div>
      </van-tab>
      
      <!-- 科目管理 -->
      <van-tab title="科目管理" name="subjects">
        <div class="tab-content">
          <div class="subject-list">
            <van-cell-group inset>
              <van-cell
                v-for="(subject, index) in subjects"
                :key="index"
                :title="subject"
              >
                <template #right-icon>
                  <van-icon name="delete-o" @click="confirmRemoveSubject(index)" />
                </template>
              </van-cell>
            </van-cell-group>
            
            <van-field
              v-model="newSubject"
              label="添加科目"
              placeholder="输入科目名称"
            >
              <template #button>
                <van-button size="small" type="primary" @click="addSubject">添加</van-button>
              </template>
            </van-field>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 导入学生弹窗 -->
    <van-dialog
      v-model:show="showImportDialog"
      title="导入学生"
      show-cancel-button
      :before-close="beforeImportClose"
    >
      <div class="import-dialog">
        <van-uploader
          v-model="importFile"
          :max-count="1"
          accept=".csv,.xlsx,.xls"
          :after-read="handleFileSelect"
        />
        <p class="import-tip">
          支持CSV和Excel格式，需包含：姓名、学号（可选）、性别（可选）
        </p>
      </div>
    </van-dialog>

    <!-- 创建小组弹窗 -->
    <van-dialog
      v-model:show="showCreateGroup"
      title="创建学习小组"
      show-cancel-button
      :before-close="beforeCreateGroupClose"
    >
      <van-field
        v-model="newGroupName"
        label="小组名称"
        placeholder="请输入小组名称"
      />
    </van-dialog>

    <!-- 添加学生到小组弹窗 -->
    <van-action-sheet
      v-model:show="showAddStudent"
      title="添加学生到小组"
    >
      <div class="student-selector">
        <van-radio-group v-model="selectedStudentId">
          <van-cell
            v-for="student in ungroupedStudents"
            :key="student.id"
            clickable
            @click="selectedStudentId = student.id"
          >
            <template #title>
              <van-radio :name="student.id">{{ student.name }}</van-radio>
            </template>
          </van-cell>
        </van-radio-group>
        <div class="action-buttons">
          <van-button type="primary" block @click="confirmAddStudent">确认添加</van-button>
        </div>
      </div>
    </van-action-sheet>

    <!-- 编辑学生弹窗 -->
    <van-dialog v-model:show="showEditStudent" title="编辑学生" show-cancel-button @confirm="saveEditStudent" :before-close="beforeEditClose">
      <div style="padding: 16px">
        <van-field v-model="editForm.name" label="姓名" placeholder="输入姓名" required />
        <van-field v-model="editForm.student_number" label="学号" placeholder="输入学号" />
        <van-field v-model="editForm.status" is-link readonly label="状态" placeholder="选择状态" @click="showStatusPicker = true" />
        <van-field v-model="editForm.study_group_name" is-link readonly label="学习小组" placeholder="选择小组" @click="showGroupPicker = true" />
        <!-- 转班目标选择 -->
        <van-field v-if="editForm.status === 'transfer'" is-link readonly label="目标班级" placeholder="选择目标班级" @click="showTransferPicker = true" :value="transferClassName" />
      </div>
    </van-dialog>

    <!-- 状态选择器 -->
    <van-popup v-model:show="showStatusPicker" position="bottom" round>
      <van-picker :columns="statusOptions" @confirm="onStatusConfirm" @cancel="showStatusPicker = false" />
    </van-popup>

    <!-- 小组选择器 -->
    <van-popup v-model:show="showGroupPicker" position="bottom" round>
      <van-picker :columns="groupOptions" @confirm="onGroupConfirm" @cancel="showGroupPicker = false" />
    </van-popup>

    <!-- 转班选择器 -->
    <van-popup v-model:show="showTransferPicker" position="bottom" round>
      <van-picker :columns="classOptions" @confirm="onTransferConfirm" @cancel="showTransferPicker = false" />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showSuccessToast, showFailToast, showToast, showConfirmDialog } from 'vant'
import { getClassDetail, getClasses, updateClassSubjects } from '@/api/schools'
import { getStudents, importStudents, updateStudent, deleteStudent, transferStudent, getStudyGroups, createStudyGroup, addStudentToGroup, removeStudentFromGroup } from '@/api/students'
import type { ClassResponse } from '@/api/schools'
import type { Student, StudyGroup } from '@/api/types'

const route = useRoute()

// 状态
const activeTab = ref('students')
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(true)
const classInfo = ref<ClassResponse | null>(null)
const students = ref<Student[]>([])
const groups = ref<StudyGroup[]>([])
const activeGroups = ref<string[]>([])

// 导入相关
const showImportDialog = ref(false)
const importFile = ref<any[]>([])

// 小组相关
const showCreateGroup = ref(false)
const newGroupName = ref('')
const showAddStudent = ref(false)
const selectedStudentId = ref('')
const currentGroupId = ref('')

// 计算未分组学生
const ungroupedStudents = computed(() => {
  return students.value.filter(s => !s.study_group_id)
})

// 获取小组名称
const getGroupName = (groupId: string) => {
  const group = groups.value.find(g => g.id === groupId)
  return group?.name || ''
}

// 加载班级信息
const loadClassInfo = async () => {
  const classId = route.params.id as string
  try {
    const response = await getClassDetail(classId)
    classInfo.value = response
  } catch (error) {
    showFailToast('获取班级信息失败')
  }
}

// 加载学生列表
const loadStudents = async () => {
  const classId = route.params.id as string
  try {
    const response = await getStudents({ class_id: classId })
    students.value = response.items
    finished.value = true
  } catch (error) {
    showFailToast('获取学生列表失败')
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 加载学习小组
const loadGroups = async () => {
  const classId = route.params.id as string
  try {
    groups.value = await getStudyGroups(classId)
  } catch (error) {
    showFailToast('获取学习小组失败')
  }
}

// 下拉刷新
const onRefresh = async () => {
  await loadStudents()
  refreshing.value = false
}

// 复制邀请码
const copyInviteCode = () => {
  if (classInfo.value?.invite_code) {
    navigator.clipboard.writeText(classInfo.value.invite_code)
    showSuccessToast('已复制邀请码')
  }
}

// 文件选择处理
const handleFileSelect = (file: any) => {
  console.log('Selected file:', file)
}

// 导入确认
const beforeImportClose = async (action: string) => {
  if (action === 'cancel') {
    importFile.value = []
    return true
  }
  
  if (!importFile.value.length) {
    showFailToast('请选择文件')
    return false
  }
  
  const classId = route.params.id as string
  try {
    const formData = new FormData()
    formData.append('class_id', classId)
    formData.append('file', importFile.value[0].file)
    
    await importStudents(formData)
    showSuccessToast('导入成功')
    importFile.value = []
    await loadStudents()
    return true
  } catch (error) {
    showFailToast('导入失败')
    return false
  }
}

// 创建小组确认
const beforeCreateGroupClose = async (action: string) => {
  if (action === 'cancel') {
    newGroupName.value = ''
    return true
  }
  
  if (!newGroupName.value.trim()) {
    showFailToast('请输入小组名称')
    return false
  }
  
  const classId = route.params.id as string
  try {
    await createStudyGroup({ class_id: classId, name: newGroupName.value })
    showSuccessToast('创建成功')
    newGroupName.value = ''
    await loadGroups()
    return true
  } catch (error) {
    showFailToast('创建失败')
    return false
  }
}

// 从小组移除学生
const removeFromGroup = async (groupId: string, studentId: string) => {
  try {
    await removeStudentFromGroup(groupId, studentId)
    showSuccessToast('移除成功')
    await Promise.all([loadStudents(), loadGroups()])
  } catch (error) {
    showFailToast('移除失败')
  }
}

// 确认添加学生到小组
const confirmAddStudent = async () => {
  if (!selectedStudentId.value) {
    showFailToast('请选择学生')
    return
  }
  
  try {
    await addStudentToGroup(currentGroupId.value, selectedStudentId.value)
    showSuccessToast('添加成功')
    showAddStudent.value = false
    selectedStudentId.value = ''
    await Promise.all([loadStudents(), loadGroups()])
  } catch (error) {
    showFailToast('添加失败')
  }
}

// ============ 学生编辑/删除 ============

const showEditStudent = ref(false)
const showStatusPicker = ref(false)
const showGroupPicker = ref(false)
const showTransferPicker = ref(false)
const transferClassId = ref('')
const transferClassName = ref('')

const editForm = reactive({
  id: '',
  name: '',
  student_number: '',
  status: 'active',
  study_group_id: '',
  study_group_name: '',
})

const statusMap: Record<string, string> = { active: '在读', leave: '请假', transfer: '转班', leave_school: '离校' }
const statusName = (s: string) => statusMap[s] || s

const statusOptions = Object.entries(statusMap).map(([v, t]) => ({ text: t, value: v }))
const groupOptions = computed(() => [
  { text: '无小组', value: '' },
  ...groups.value.map(g => ({ text: g.name, value: g.id }))
])
const classOptions = ref<Array<{ text: string; value: string }>>([])

function openEditStudent(student: any) {
  editForm.id = student.id
  editForm.name = student.name
  editForm.student_number = student.student_number || ''
  editForm.status = student.status || 'active'
  editForm.study_group_id = student.study_group_id || ''
  editForm.study_group_name = getGroupName(student.study_group_id) || '无小组'
  transferClassId.value = ''
  transferClassName.value = ''
  showEditStudent.value = true
}

function onStatusConfirm({ selectedOptions }: any) {
  editForm.status = selectedOptions[0].value
  editForm.study_group_name = statusMap[editForm.status] || editForm.status
  showStatusPicker.value = false
}

function onGroupConfirm({ selectedOptions }: any) {
  editForm.study_group_id = selectedOptions[0].value
  editForm.study_group_name = selectedOptions[0].text
  showGroupPicker.value = false
}

async function onTransferConfirm({ selectedOptions }: any) {
  transferClassId.value = selectedOptions[0].value
  transferClassName.value = selectedOptions[0].text
  showTransferPicker.value = false
}

function beforeEditClose(action: string, done: () => void) {
  if (action === 'confirm') {
    saveEditStudent().then(done).catch(() => {})
  } else {
    done()
  }
}

async function saveEditStudent() {
  try {
    if (editForm.status === 'transfer' && transferClassId.value) {
      await transferStudent(editForm.id, transferClassId.value)
      showToast('转班成功')
    } else {
      await updateStudent(editForm.id, {
        name: editForm.name,
        student_number: editForm.student_number || undefined,
        study_group_id: editForm.study_group_id || undefined,
        status: editForm.status
      })
      showToast('保存成功')
    }
    loadStudents()
  } catch (e: any) {
    showToast(e?.message || '保存失败')
    throw e
  }
}

async function confirmDeleteStudent(student: any) {
  try {
    await showConfirmDialog({
      title: '删除学生',
      message: `删除「${student.name}」后，该学生的所有数据（任务提交、评价记录等）将无法恢复。确认删除？`,
      confirmButtonText: '确认删除',
      confirmButtonColor: '#ee0a24'
    })
    await deleteStudent(student.id)
    showToast('已删除')
    loadStudents()
  } catch (e: any) {
    if (e !== 'confirm') showToast(e?.message || '删除失败')
  }
}

// 加载班级列表（用于转班选择）
async function loadClassOptions() {
  try {
    const data = await getClasses()
    classOptions.value = data
      .filter((c: any) => c.id !== route.params.id)
      .map((c: any) => ({ text: c.name, value: c.id }))
  } catch {}
}

// ========== 科目管理 ==========
const subjects = ref<string[]>([])
const newSubject = ref('')

// 加载科目列表
async function loadSubjects() {
  if (classInfo.value?.subjects) {
    subjects.value = [...classInfo.value.subjects]
  }
}

// 添加科目
async function addSubject() {
  if (!newSubject.value.trim()) {
    showToast('请输入科目名称')
    return
  }
  
  if (subjects.value.includes(newSubject.value.trim())) {
    showToast('科目已存在')
    return
  }
  
  const newSubjects = [...subjects.value, newSubject.value.trim()]
  
  // 保存到后端
  try {
    await updateClassSubjects(route.params.id as string, newSubjects)
    subjects.value = newSubjects
    newSubject.value = ''
    showSuccessToast('科目添加成功')
  } catch (error) {
    showFailToast('保存失败')
  }
}

// 删除科目
async function confirmRemoveSubject(index: number) {
  try {
    await showConfirmDialog({
      title: '删除科目',
      message: `确认删除「${subjects.value[index]}」科目？`,
      confirmButtonText: '确认删除',
      confirmButtonColor: '#ee0a24'
    })
    
    const newSubjects = subjects.value.filter((_, i) => i !== index)
    await updateClassSubjects(route.params.id as string, newSubjects)
    subjects.value = newSubjects
    showSuccessToast('已删除')
  } catch (e) {
    // 取消删除
  }
}

// 初始化
onMounted(async () => {
  await loadClassInfo()
  await loadStudents()
  await loadGroups()
  await loadClassOptions()
  await loadSubjects()
})
</script>

<style scoped>
.class-detail {
  padding: 12px;
  padding-bottom: 60px;
}

.info-card {
  margin-bottom: 12px;
}

.tab-content {
  padding: 12px;
  background: #f7f8fa;
  min-height: calc(100vh - 300px);
}

.action-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.import-dialog {
  padding: 16px;
}

.import-tip {
  margin-top: 12px;
  font-size: 12px;
  color: #999;
}

.student-selector {
  padding: 12px;
  max-height: 50vh;
  overflow-y: auto;
}

.student-actions {
  display: flex;
  align-items: center;
}

.action-buttons {
  padding: 12px;
}
</style>
