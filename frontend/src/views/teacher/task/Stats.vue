<template>
  <div class="task-stats-page">
    <!-- 筛选栏 -->
    <van-cell-group inset class="filter-section">
      <van-field
        v-model="selectedClassLabel"
        is-link
        readonly
        label="班级"
        placeholder="选择班级"
        @click="showClassPicker = true"
      />
      <van-field
        v-model="selectedPeriod"
        is-link
        readonly
        label="时间范围"
        placeholder="选择时间范围"
        @click="showPeriodPicker = true"
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
        v-model="selectedGroupLabel"
        is-link
        readonly
        label="组别"
        placeholder="全部组别"
        @click="showGroupPicker = true"
      />
    </van-cell-group>

    <!-- 数据卡片 -->
    <van-cell-group inset class="stats-cards">
      <div class="cards-grid">
        <div class="card-item">
          <div class="card-value">{{ stats.total }}</div>
          <div class="card-label">总任务数</div>
        </div>
        <div class="card-item">
          <div class="card-value">{{ stats.weekCount }}</div>
          <div class="card-label">本周任务</div>
        </div>
        <div class="card-item">
          <div class="card-value">{{ stats.avgCompletionRate }}%</div>
          <div class="card-label">平均提交率</div>
        </div>
        <div class="card-item">
          <div class="card-value">{{ stats.unsubmittedCount }}</div>
          <div class="card-label">未提交人数</div>
        </div>
      </div>
    </van-cell-group>

    <!-- 科目统计柱状图 -->
    <div class="section-title">各科目提交率</div>
    <van-cell-group inset class="chart-section">
      <div v-if="stats.bySubject.length > 0" class="bar-chart">
        <div v-for="item in stats.bySubject" :key="item.subject" class="bar-row">
          <div class="bar-label">{{ item.subject }}</div>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: `${item.completionRate}%`, background: getSubjectColor(item.subject) }">
              <span v-if="item.completionRate > 15" class="bar-text">{{ item.completionRate }}%</span>
            </div>
            <span v-if="item.completionRate <= 15" class="bar-text-outside">{{ item.completionRate }}%</span>
          </div>
          <div class="bar-count">{{ item.count }}个</div>
        </div>
      </div>
      <van-empty v-else description="暂无数据" :image-size="60" />
    </van-cell-group>

    <!-- 组别统计 -->
    <div class="section-title">各小组提交率</div>
    <van-cell-group inset>
      <van-cell
        v-for="group in stats.byGroup"
        :key="group.name"
        :title="group.name"
        :label="`学生${group.count}人`"
      >
        <template #value>
          <div class="group-stat">
            <van-progress
              :percentage="group.completionRate"
              :stroke-width="6"
              color="#3e7dc9"
              style="width: 80px"
            />
            <span class="rate-text">{{ group.completionRate }}%</span>
          </div>
        </template>
      </van-cell>
      <van-empty v-if="stats.byGroup.length === 0" description="暂无数据" :image-size="60" />
    </van-cell-group>

    <!-- 完成趋势折线图 -->
    <div class="section-title">提交趋势</div>
    <van-cell-group inset class="chart-section">
      <div v-if="stats.trend.length > 0" class="trend-chart">
        <div class="trend-container">
          <div v-for="(item, index) in stats.trend" :key="index" class="trend-point">
            <div class="trend-bar-wrapper">
              <div class="trend-value">{{ item.percentage }}%</div>
              <div class="trend-bar" :style="{ height: `${Math.max(item.percentage, 3)}%` }"></div>
            </div>
            <div class="trend-label">{{ item.label }}</div>
          </div>
        </div>
      </div>
      <van-empty v-else description="暂无数据" :image-size="60" />
    </van-cell-group>

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

    <!-- 组别选择器 -->
    <van-popup v-model:show="showGroupPicker" position="bottom" round>
      <van-picker
        :columns="groupColumns"
        title="选择组别"
        @confirm="onGroupConfirm"
        @cancel="showGroupPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showFailToast } from 'vant'
import { getTaskStatsDetail, type TaskStatsDetail } from '@/api/tasks'
import { getClasses } from '@/api/schools'
import { http } from '@/utils/request'
import { SUBJECT_COLORS } from '@/constants'
import type { Class, StudyGroup } from '@/api/types'

// 状态
const classes = ref<Class[]>([])
const studyGroups = ref<StudyGroup[]>([])
const selectedClassId = ref('')
const selectedClassLabel = ref('')
const selectedPeriod = ref('本周')
const selectedPeriodValue = ref<'yesterday' | 'week' | 'month' | 'all'>('week')
const selectedSubject = ref('')
const selectedGroupId = ref('')
const selectedGroupLabel = ref('')
const loading = ref(false)

// 弹窗
const showClassPicker = ref(false)
const showPeriodPicker = ref(false)
const showSubjectPicker = ref(false)
const showGroupPicker = ref(false)

// 统计数据
const stats = ref<TaskStatsDetail>({
  total: 0,
  weekCount: 0,
  avgCompletionRate: 0,
  unsubmittedCount: 0,
  bySubject: [],
  byGroup: [],
  trend: []
})

// 可用科目
const availableSubjects = computed(() => {
  const cls = classes.value.find(c => c.id === selectedClassId.value)
  return cls?.subjects || ['语文', '数学', '英语']
})

// 选择器列
const classColumns = computed(() => classes.value.map(c => ({ text: c.name, value: c.id })))
const periodColumns = [
  { text: '昨天', value: 'yesterday' },
  { text: '本周', value: 'week' },
  { text: '本月', value: 'month' },
  { text: '全部', value: 'all' },
]
const subjectColumns = computed(() => {
  const cols = [{ text: '全部科目', value: '' }]
  availableSubjects.value.forEach(s => cols.push({ text: s, value: s }))
  return cols
})
const groupColumns = computed(() => {
  const cols = [{ text: '全部组别', value: '' }]
  studyGroups.value.forEach(g => cols.push({ text: g.name, value: g.id }))
  return cols
})

// 获取科目颜色
const getSubjectColor = (subject: string) => SUBJECT_COLORS[subject] || '#909399'

// 加载统计
const loadStats = async () => {
  if (!selectedClassId.value) return
  loading.value = true
  try {
    const params: any = {
      class_id: selectedClassId.value,
      period: selectedPeriodValue.value
    }
    if (selectedSubject.value) params.subject = selectedSubject.value
    if (selectedGroupId.value) params.group_id = selectedGroupId.value
    
    stats.value = await getTaskStatsDetail(params)
  } catch (error) {
    showFailToast('加载统计失败')
  } finally {
    loading.value = false
  }
}

// 加载小组
const loadStudyGroups = async () => {
  if (!selectedClassId.value) return
  try {
    const res = await http.get<StudyGroup[]>(`/schools/classes/${selectedClassId.value}/groups`)
    studyGroups.value = res || []
  } catch { studyGroups.value = [] }
}

// 选择器回调
const onClassConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedClassId.value = selected.value
  selectedClassLabel.value = selected.text
  showClassPicker.value = false
  selectedSubject.value = ''
  selectedGroupId.value = ''
  selectedGroupLabel.value = ''
  loadStudyGroups()
  loadStats()
}

const onPeriodConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedPeriod.value = selected.text
  selectedPeriodValue.value = selected.value
  showPeriodPicker.value = false
  loadStats()
}

const onSubjectConfirm = ({ selectedOptions }: any) => {
  selectedSubject.value = selectedOptions[0].value
  showSubjectPicker.value = false
  loadStats()
}

const onGroupConfirm = ({ selectedOptions }: any) => {
  selectedGroupId.value = selectedOptions[0].value
  selectedGroupLabel.value = selectedOptions[0].text
  showGroupPicker.value = false
  loadStats()
}

onMounted(async () => {
  try {
    classes.value = await getClasses()
    if (classes.value.length > 0) {
      selectedClassId.value = classes.value[0].id
      selectedClassLabel.value = classes.value[0].name
      await loadStudyGroups()
      await loadStats()
    }
  } catch { showFailToast('加载失败') }
})
</script>

<style scoped lang="scss">
.task-stats-page {
  padding: 12px;
  padding-bottom: 80px;
  
  .filter-section { margin-bottom: 12px; }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .stats-cards {
    padding: 16px;
    margin-bottom: 12px;
    
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      
      .card-item {
        text-align: center;
        
        .card-value {
          font-size: 22px;
          font-weight: 600;
          color: #3e7dc9;
        }
        
        .card-label {
          font-size: 11px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
  
  .chart-section {
    padding: 16px;
    min-height: 100px;
  }
  
  .bar-chart {
    .bar-row {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      
      .bar-label {
        width: 50px;
        font-size: 13px;
        color: #606266;
        flex-shrink: 0;
      }
      
      .bar-track {
        flex: 1;
        height: 24px;
        background: #f5f7fa;
        border-radius: 4px;
        overflow: hidden;
        position: relative;
        
        .bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.5s ease;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          padding-right: 6px;
          
          .bar-text {
            font-size: 11px;
            color: #fff;
            white-space: nowrap;
          }
        }
        
        .bar-text-outside {
          font-size: 11px;
          color: #606266;
          margin-left: 4px;
          white-space: nowrap;
        }
      }
      
      .bar-count {
        width: 40px;
        font-size: 11px;
        color: #909399;
        text-align: right;
        flex-shrink: 0;
      }
    }
  }
  
  .group-stat {
    display: flex;
    align-items: center;
    gap: 6px;
    
    .rate-text {
      font-size: 12px;
      color: #3e7dc9;
      white-space: nowrap;
    }
  }
  
  .trend-chart {
    .trend-container {
      display: flex;
      align-items: flex-end;
      height: 150px;
      gap: 4px;
      
      .trend-point {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
        
        .trend-bar-wrapper {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-end;
          width: 100%;
          
          .trend-value {
            font-size: 10px;
            color: #606266;
            margin-bottom: 4px;
            white-space: nowrap;
          }
          
          .trend-bar {
            width: 20px;
            background: linear-gradient(to top, #3e7dc9, #6db3f2);
            border-radius: 3px 3px 0 0;
            min-height: 3px;
            transition: height 0.5s ease;
          }
        }
        
        .trend-label {
          margin-top: 6px;
          font-size: 10px;
          color: #909399;
          white-space: nowrap;
        }
      }
    }
  }
}
</style>
