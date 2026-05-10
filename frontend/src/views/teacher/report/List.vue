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
        :label="`完成率: ${subject.completionRate}%`"
      >
        <template #value>
          <div class="subject-stats">
            <span>{{ subject.taskCount }}个任务</span>
            <van-progress
              :percentage="subject.completionRate"
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
        :label="`完成任务: ${student.taskCount}个`"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { getClasses } from '@/api/schools'
import type { Class } from '@/api/types'

// 状态
const classes = ref<Class[]>([])
const selectedClass = ref('')
const selectedClassId = ref('')
const selectedPeriod = ref('本周')
const showClassPicker = ref(false)
const showPeriodPicker = ref(false)
const chartType = ref('task')

// 总览数据
const overview = reactive({
  totalStudents: 42,
  activeStudents: 38,
  taskCompletion: 78,
  avgDuration: 25
})

// 趋势数据
const trendData = ref([
  { label: '周一', count: 35, percentage: 70 },
  { label: '周二', count: 42, percentage: 84 },
  { label: '周三', count: 38, percentage: 76 },
  { label: '周四', count: 45, percentage: 90 },
  { label: '周五', count: 40, percentage: 80 },
  { label: '周六', count: 25, percentage: 50 },
  { label: '周日', count: 20, percentage: 40 }
])

// 评价分布
const evaluationDistribution = ref([
  { level: '优秀', count: 12, percentage: 28, color: '#07c160' },
  { level: '良好', count: 18, percentage: 43, color: '#3e7dc9' },
  { level: '一般', count: 10, percentage: 24, color: '#ff976a' },
  { level: '待提高', count: 2, percentage: 5, color: '#ee0a24' }
])

// 科目统计
const subjectStats = ref([
  { name: '语文', taskCount: 8, completionRate: 82 },
  { name: '数学', taskCount: 6, completionRate: 75 },
  { name: '英语', taskCount: 5, completionRate: 70 },
  { name: '科学', taskCount: 5, completionRate: 68 }
])

// 学生排行
const studentRanking = ref([
  { id: '1', name: '张三', taskCount: 24, rating: 5 },
  { id: '2', name: '李四', taskCount: 22, rating: 5 },
  { id: '3', name: '王五', taskCount: 20, rating: 4 },
  { id: '4', name: '赵六', taskCount: 18, rating: 4 },
  { id: '5', name: '钱七', taskCount: 16, rating: 4 }
])

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
    }
  } catch (error) {
    showFailToast('加载班级失败')
  }
}

// 导出报告
const exportReport = async () => {
  showSuccessToast('报告生成中...')
  // TODO: 调用后端API生成报告
}

// 班级确认
const onClassConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedClass.value = selected.text
  selectedClassId.value = selected.value
  showClassPicker.value = false
  // TODO: 重新加载数据
}

// 时间范围确认
const onPeriodConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedPeriod.value = selected.text
  showPeriodPicker.value = false
  // TODO: 重新加载数据
}

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
