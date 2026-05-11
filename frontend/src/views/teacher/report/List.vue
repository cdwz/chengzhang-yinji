<template>
  <div class="report-list">
    <!-- 筛选 -->
    <van-cell-group inset class="filter-section">
      <van-field
        v-model="selectedClass"
        is-link
        readonly
        label="班级"
        placeholder="选择班级"
        @click="showClassPicker = true"
      />
      <van-field
        v-model="selectedSubject"
        is-link
        readonly
        label="科目"
        placeholder="全部科目"
        @click="showSubjectPicker = true"
      />
      <van-field
        v-model="selectedGroupName"
        is-link
        readonly
        label="学习小组"
        placeholder="全部小组"
        @click="showGroupPicker = true"
      />
      <van-field
        v-model="selectedPeriod"
        is-link
        readonly
        label="时间范围"
        placeholder="选择时间范围"
        @click="showPeriodPicker = true"
      />
    </van-cell-group>

    <!-- 总览卡片 -->
    <van-cell-group inset class="overview-section">
      <div class="overview-title">学习情况总览</div>
      <div class="overview-grid">
        <div class="overview-item">
          <div class="overview-value">{{ overview.totalStudents }}</div>
          <div class="overview-label">学生总数</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ overview.activeStudents }}</div>
          <div class="overview-label">活跃学生</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ overview.taskCompletion }}%</div>
          <div class="overview-label">任务完成率</div>
        </div>
        <div class="overview-item">
          <div class="overview-value">{{ overview.avgDuration }}分钟</div>
          <div class="overview-label">平均学习时长</div>
        </div>
      </div>
    </van-cell-group>

    <!-- 趋势图表 -->
    <div class="section-title">学习趋势</div>
    <van-cell-group inset class="chart-section">
      <van-tabs v-model:active="chartType" sticky>
        <van-tab title="任务完成趋势" name="task">
          <div class="chart-container">
            <div class="simple-chart">
              <div
                v-for="(item, index) in trendData"
                :key="index"
                class="chart-bar-wrapper"
              >
                <div class="chart-bar" :style="{ height: `${item.percentage}%` }">
                  <span class="bar-value">{{ item.count }}</span>
                </div>
                <div class="bar-label">{{ item.label }}</div>
              </div>
            </div>
          </div>
        </van-tab>
        
        <van-tab title="评价分布" name="evaluation">
          <div class="chart-container">
            <div class="distribution-list">
              <div v-for="item in evaluationDistribution" :key="item.level" class="distribution-item">
                <span class="level-label">{{ item.level }}</span>
                <van-progress :percentage="item.percentage" :color="item.color" />
                <span class="count-label">{{ item.count }}人</span>
              </div>
            </div>
          </div>
        </van-tab>
      </van-tabs>
    </van-cell-group>

    <!-- 科目分析 -->
    <div class="section-title">各科目情况</div>
    <van-cell-group inset>
      <van-cell
        v-for="subject in subjectStats"
        :key="subject.name"
        :title="subject.name"
        :label="`完成率: ${subject.completion_rate}%`"
      >
        <template #value>
          <div class="subject-stats">
            <span>{{ subject.task_count }}个任务</span>
            <van-progress
              :percentage="subject.completion_rate"
              :stroke-width="6"
              color="#3e7dc9"
            />
          </div>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 学生排行 -->
    <div class="section-title">学生排行</div>
    <van-cell-group inset>
      <van-cell
        v-for="(student, index) in studentRanking"
        :key="student.id"
        :title="student.name"
        :label="`完成任务: ${student.task_count}个`"
      >
        <template #icon>
          <van-tag :type="getRankType(index)" size="medium">
            {{ index + 1 }}
          </van-tag>
        </template>
        <template #value>
          <van-rate v-model="student.rating" readonly size="12" />
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 导出按钮 -->
    <div class="export-section">
      <van-button type="primary" block @click="exportReport">
        导出报告
      </van-button>
    </div>

    <!-- 班级选择器 -->
    <van-popup v-model:show="showClassPicker" position="bottom" round>
      <van-picker
        :columns="classColumns"
        title="选择班级"
        @confirm="onClassConfirm"
        @cancel="showClassPicker = false"
      />
    </van-popup>

    <!-- 时间范围选择器 -->
    <van-popup v-model:show="showPeriodPicker" position="bottom" round>
      <van-picker
        :columns="periodColumns"
        title="选择时间范围"
        @confirm="onPeriodConfirm"
        @cancel="showPeriodPicker = false"
      />
    </van-popup>
    
    <!-- 科目选择器 -->
    <van-popup v-model:show="showSubjectPicker" position="bottom" round>
      <van-picker
        :columns="subjectColumns"
        title="选择科目"
        @confirm="onSubjectConfirm"
        @cancel="showSubjectPicker = false"
      />
    </van-popup>
    
    <!-- 学习小组选择器 -->
    <van-popup v-model:show="showGroupPicker" position="bottom" round>
      <van-picker
        :columns="groupColumns"
        title="选择学习小组"
        @confirm="onGroupConfirm"
        @cancel="showGroupPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { getClasses, getClass } from '@/api/schools'
import { getClassReport, exportClassPdf } from '@/api/reports'
import { getStudyGroups } from '@/api/students'
import type { Class, StudyGroup } from '@/api/types'

// 状态
const classes = ref<Class[]>([])
const selectedClass = ref('')
const selectedClassId = ref('')
const selectedPeriod = ref('本周')
const selectedPeriodValue = ref<'week' | 'month' | 'semester'>('week')
const showClassPicker = ref(false)
const showPeriodPicker = ref(false)
const showSubjectPicker = ref(false)
const showGroupPicker = ref(false)
const chartType = ref('task')
const loading = ref(false)

// 科目筛选
const classSubjects = ref<string[]>([])
const selectedSubject = ref('')
const selectedSubjectValue = ref<string>('')

// 学习小组筛选
const studyGroups = ref<StudyGroup[]>([])
const selectedGroupName = ref('')
const selectedGroupId = ref<string>('')

// 总览数据
const overview = reactive({
  totalStudents: 0,
  activeStudents: 0,
  taskCompletion: 0,
  avgDuration: 0
})

// 趋势数据
const trendData = ref<Array<{ label: string; count: number; percentage: number }>>([])

// 评价分布
const evaluationDistribution = ref<Array<{ level: string; count: number; percentage: number; color: string }>>([])

// 科目统计
const subjectStats = ref<Array<{ name: string; task_count: number; completion_rate: number }>>([])

// 学生排行
const studentRanking = ref<Array<{ id: string; name: string; task_count: number; rating: number }>>([])

// 班级选择器列
const classColumns = computed(() => {
  return classes.value.map(c => ({
    text: c.name,
    value: c.id
  }))
})

// 时间范围选项
const periodColumns = [
  { text: '本周', value: 'week' },
  { text: '本月', value: 'month' },
  { text: '本学期', value: 'semester' }
]

// 科目选择器列
const subjectColumns = computed(() => {
  const cols = [{ text: '全部科目', value: '' }]
  classSubjects.value.forEach(s => {
    cols.push({ text: s, value: s })
  })
  return cols
})

// 学习小组选择器列
const groupColumns = computed(() => {
  const cols = [{ text: '全部小组', value: '' }]
  studyGroups.value.forEach(g => {
    cols.push({ text: g.name, value: g.id })
  })
  return cols
})

// 获取排行标签类型
const getRankType = (index: number) => {
  if (index === 0) return 'danger'
  if (index === 1) return 'warning'
  if (index === 2) return 'primary'
  return 'default'
}

// 加载班级列表
const loadClasses = async () => {
  try {
    classes.value = await getClasses()
    if (classes.value.length > 0) {
      const first = classes.value[0]
      selectedClass.value = first.name
      selectedClassId.value = first.id
      loadClassData()
      loadReportData()
    }
  } catch (error) {
    showFailToast('加载班级失败')
  }
}

// 加载班级数据（科目、小组）
const loadClassData = async () => {
  if (!selectedClassId.value) return
  
  try {
    // 加载班级详情获取科目
    const classDetail = await getClass(selectedClassId.value)
    classSubjects.value = classDetail.subjects || ['语文', '数学', '英语']
    
    // 加载学习小组
    studyGroups.value = await getStudyGroups(selectedClassId.value)
  } catch (error) {
    console.error('加载班级数据失败', error)
  }
}

// 加载报告数据
const loadReportData = async () => {
  if (!selectedClassId.value) return
  
  loading.value = true
  try {
    const params: any = {
      class_id: selectedClassId.value,
      period: selectedPeriodValue.value
    }
    
    // 添加筛选参数
    if (selectedSubjectValue.value) {
      params.subject = selectedSubjectValue.value
    }
    if (selectedGroupId.value) {
      params.study_group_id = selectedGroupId.value
    }
    
    const data = await getClassReport(params)
    
    // 更新数据
    overview.totalStudents = data.overview.total_students
    overview.activeStudents = data.overview.active_students
    overview.taskCompletion = data.overview.task_completion
    overview.avgDuration = data.overview.avg_duration
    
    trendData.value = data.trend
    evaluationDistribution.value = data.distribution
    subjectStats.value = data.subjects
    studentRanking.value = data.ranking
  } catch (error) {
    showFailToast('加载报告失败')
  } finally {
    loading.value = false
  }
}

// 导出报告
const exportReport = async () => {
  if (!selectedClassId.value) {
    showFailToast('请选择班级')
    return
  }
  
  try {
    const blob = await exportClassPdf({
      class_id: selectedClassId.value,
      period: selectedPeriodValue.value
    })
    
    // 下载文件
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedClass.value}-${selectedPeriod.value}报告.pdf`
    a.click()
    URL.revokeObjectURL(url)
    
    showSuccessToast('导出成功')
  } catch (error) {
    showFailToast('导出失败')
  }
}

// 班级确认
const onClassConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedClass.value = selected.text
  selectedClassId.value = selected.value
  showClassPicker.value = false
  // 重置筛选
  selectedSubject.value = ''
  selectedSubjectValue.value = ''
  selectedGroupName.value = ''
  selectedGroupId.value = ''
  loadClassData()
  loadReportData()
}

// 科目确认
const onSubjectConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedSubject.value = selected.text === '全部科目' ? '' : selected.text
  selectedSubjectValue.value = selected.value
  showSubjectPicker.value = false
  loadReportData()
}

// 学习小组确认
const onGroupConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedGroupName.value = selected.text === '全部小组' ? '' : selected.text
  selectedGroupId.value = selected.value
  showGroupPicker.value = false
  loadReportData()
}

// 时间范围确认
const onPeriodConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedPeriod.value = selected.text
  selectedPeriodValue.value = selected.value
  showPeriodPicker.value = false
  loadReportData()
}

// 监听班级和周期变化
watch([selectedClassId, selectedPeriodValue], () => {
  if (selectedClassId.value) {
    loadReportData()
  }
})

// 初始化
onMounted(() => {
  loadClasses()
})
</script>

<style scoped lang="scss">
.report-list {
  padding: 12px;
  padding-bottom: 80px;
  
  .filter-section {
    margin-bottom: 12px;
  }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .overview-section {
    padding: 16px;
    
    .overview-title {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 16px;
    }
    
    .overview-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      
      .overview-item {
        text-align: center;
        
        .overview-value {
          font-size: 24px;
          font-weight: 600;
          color: #3e7dc9;
        }
        
        .overview-label {
          font-size: 12px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
  
  .chart-section {
    .chart-container {
      padding: 16px;
      min-height: 200px;
      
      .simple-chart {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 150px;
        
        .chart-bar-wrapper {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          
          .chart-bar {
            width: 24px;
            background: linear-gradient(to top, #3e7dc9, #6db3f2);
            border-radius: 4px 4px 0 0;
            position: relative;
            min-height: 10px;
            
            .bar-value {
              position: absolute;
              top: -20px;
              left: 50%;
              transform: translateX(-50%);
              font-size: 12px;
              color: #606266;
            }
          }
          
          .bar-label {
            margin-top: 8px;
            font-size: 10px;
            color: #909399;
          }
        }
      }
      
      .distribution-list {
        .distribution-item {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
          
          .level-label {
            width: 60px;
            font-size: 14px;
          }
          
          .van-progress {
            flex: 1;
            margin: 0 12px;
          }
          
          .count-label {
            width: 50px;
            text-align: right;
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
  }
  
  .subject-stats {
    text-align: right;
    
    .van-progress {
      margin-top: 4px;
    }
  }
  
  .export-section {
    padding: 16px;
  }
}
</style>
