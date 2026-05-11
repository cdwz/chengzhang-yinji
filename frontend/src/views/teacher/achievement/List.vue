<template>
  <div class="teacher-achievements">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学生成就</span>
        </div>
      </template>

      <!-- 班级选择 -->
      <div class="filter-row">
        <el-select v-model="selectedClassId" placeholder="选择班级" style="width: 150px" @change="onClassChange">
          <el-option v-for="cls in classes" :key="cls.id" :label="cls.name" :value="cls.id" />
        </el-select>
        
        <el-select v-model="selectedSubject" placeholder="全部科目" style="width: 120px" clearable @change="loadData">
          <el-option v-for="subject in classSubjects" :key="subject" :label="subject" :value="subject" />
        </el-select>
        
        <el-select v-model="selectedGroupId" placeholder="全部小组" style="width: 120px" clearable @change="loadData">
          <el-option v-for="group in studyGroups" :key="group.id" :label="group.name" :value="group.id" />
        </el-select>
      </div>

      <!-- 成就类型概览 -->
      <el-row :gutter="16" v-if="achievementTypes.length > 0" style="margin-bottom: 20px">
        <el-col :span="6" v-for="type in achievementTypes" :key="type.key">
          <el-statistic :title="type.name" :value="type.count || 0">
            <template #suffix>人次</template>
          </el-statistic>
        </el-col>
      </el-row>

      <!-- 学生成就列表 -->
      <el-table :data="students" v-loading="loading" @row-click="viewStudentAchievements">
        <el-table-column prop="name" label="学生姓名" />
        <el-table-column prop="student_number" label="学号" width="120" />
        <el-table-column label="获得成就数" width="120">
          <template #default="{ row }">{{ row.achievement_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="checkAchievements(row)">检查新成就</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 学生成就详情弹窗 -->
    <el-dialog v-model="showDetail" :title="`${currentStudent?.name}的成就`" width="600px">
      <el-empty v-if="!studentAchievements.length" description="暂无成就记录" />
      <el-timeline v-else>
        <el-timeline-item
          v-for="ach in studentAchievements"
          :key="ach.id"
          :timestamp="ach.created_at"
          placement="top"
        >
          <el-card shadow="hover">
            <h4>{{ ach.achievement_type }}</h4>
            <p style="color:#909399">{{ ach.description || '—' }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getClasses, getClass } from '@/api/schools'
import { getStudents, getStudyGroups } from '@/api/students'
import { http } from '@/utils/request'

const classes = ref<any[]>([])
const selectedClassId = ref('')
const students = ref<any[]>([])
const loading = ref(false)
const achievementTypes = ref<any[]>([])
const showDetail = ref(false)
const currentStudent = ref<any>(null)
const studentAchievements = ref<any[]>([])

// 科目和小组筛选
const classSubjects = ref<string[]>([])
const selectedSubject = ref('')
const studyGroups = ref<any[]>([])
const selectedGroupId = ref('')

async function onClassChange() {
  // 重置筛选
  selectedSubject.value = ''
  selectedGroupId.value = ''
  
  // 加载班级数据
  try {
    const classDetail = await getClass(selectedClassId.value)
    classSubjects.value = classDetail.subjects || ['语文', '数学', '英语']
    studyGroups.value = await getStudyGroups(selectedClassId.value)
  } catch {
    console.error('加载班级数据失败')
  }
  
  loadData()
}

async function loadData() {
  if (!selectedClassId.value) return
  loading.value = true
  try {
    const params: any = { class_id: selectedClassId.value, page_size: 100 }
    if (selectedGroupId.value) {
      params.study_group_id = selectedGroupId.value
    }
    const data = await getStudents(params)
    students.value = data.items || []
    // 加载成就类型
    const types = await http.get<any[]>('/achievements/types')
    achievementTypes.value = types || []
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

async function viewStudentAchievements(student: any) {
  currentStudent.value = student
  showDetail.value = true
  try {
    const data = await http.get<any[]>(`/achievements/student/${student.id}`)
    studentAchievements.value = data || []
  } catch { studentAchievements.value = [] }
}

async function checkAchievements(student: any) {
  try {
    await http.post(`/achievements/check/${student.id}`)
    ElMessage.success('成就检查完成')
    loadData()
  } catch { ElMessage.error('检查失败') }
}

onMounted(async () => {
  classes.value = await getClasses()
  if (classes.value.length > 0) {
    selectedClassId.value = classes.value[0].id
    await onClassChange()
  }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
</style>
