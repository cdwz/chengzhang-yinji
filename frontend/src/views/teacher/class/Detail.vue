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
                :label="`学号: ${student.student_number || '未设置'}`"
                is-link
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
                  <van-tag v-if="student.study_group_id" type="primary">
                    {{ getGroupName(student.study_group_id) }}
                  </van-tag>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { getClassDetail } from '@/api/schools'
import { getStudents, importStudents } from '@/api/students'
import { getStudyGroups, createStudyGroup, addStudentToGroup, removeStudentFromGroup } from '@/api/students'
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

// 初始化
onMounted(async () => {
  await loadClassInfo()
  await loadStudents()
  await loadGroups()
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

.action-buttons {
  padding: 12px;
}
</style>
