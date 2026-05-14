<template>
  <div class="evaluation-calendar">
    <!-- 日历 -->
    <van-calendar
      :show-title="false"
      :poppable="false"
      :show-confirm="false"
      :min-date="minDate"
      :max-date="maxDate"
      :style="{ height: '350px' }"
      @select="onDateSelect"
    >
      <template #bottom-info="day">
        <div v-if="hasEvaluation(day.date)" class="dot-indicator"></div>
      </template>
    </van-calendar>

    <!-- 选中日期的评价记录 -->
    <div class="section-title">{{ selectedDateLabel }}的评价记录</div>
    
    <van-pull-refresh v-model="refreshing" @refresh="loadEvaluations">
      <div v-if="evaluations.length > 0" class="evaluation-list">
        <van-cell-group inset>
          <van-cell
            v-for="record in evaluations"
            :key="record.id"
            :title="getDimensionName(record.dimension_id)"
            :label="formatTime(record.updated_at)"
          >
            <template #value>
              <component
                :is="getRatingDisplay(record)"
                :value="record.value"
                readonly
              />
            </template>
          </van-cell>
        </van-cell-group>
      </div>
      
      <van-empty v-else description="当日暂无评价记录" />
    </van-pull-refresh>

    <!-- 统计概览 -->
    <div class="section-title">本月统计</div>
    <van-cell-group inset class="stats-section">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总评价数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.days }}</div>
          <div class="stat-label">评价天数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.excellent }}</div>
          <div class="stat-label">优秀评价</div>
        </div>
      </div>
    </van-cell-group>
    
    <!-- 班级整体情况 -->
    <div class="section-title" v-if="classStats.avg_rating">班级整体情况</div>
    <van-cell-group inset v-if="classStats.avg_rating" class="class-stats">
      <van-cell title="班级平均星级" :value="classStats.avg_rating + ' ⭐'" />
      <van-cell title="班级总评价数" :value="classStats.total_records" />
      <van-cell title="班级学生数" :value="classStats.total_students" />
    </van-cell-group>
    
    <!-- 我的孩子信息 -->
    <div class="my-child-info" v-if="myChildName">
      <van-tag type="success">我的孩子：{{ myChildName }}</van-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { showFailToast } from 'vant'
import { http } from '@/utils/request'
import type { EvaluationRecord, EvaluationDimension } from '@/api/types'

// 状态
const refreshing = ref(false)
const selectedDate = ref(new Date())
const evaluations = ref<EvaluationRecord[]>([])
const dimensions = ref<EvaluationDimension[]>([])
const evaluationDates = ref<Set<string>>(new Set())

// 我的孩子信息
const myChildName = ref('')
const myChildId = ref('')

// 班级统计
const classStats = reactive({
  avg_rating: null as number | null,
  total_records: 0,
  total_students: 0
})

// 日期范围
const minDate = new Date(2024, 0, 1)
const maxDate = new Date()

// 选中日期标签
const selectedDateLabel = computed(() => {
  const d = selectedDate.value
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

// 检查日期是否有评价
const hasEvaluation = (date: Date) => {
  const dateStr = formatDate(date)
  return evaluationDates.value.has(dateStr)
}

// 获取维度名称
const getDimensionName = (dimensionId: string) => {
  const dim = dimensions.value.find(d => d.id === dimensionId)
  return dim?.name || '未知评价'
}

// 获取评分显示组件
const getRatingDisplay = (eval_: EvaluationRecord) => {
  const dim = dimensions.value.find(d => d.id === eval_.dimension_id)
  switch (dim?.type) {
    case 'star':
      return 'van-rate'
    default:
      return 'van-tag'
  }
}

// 格式化时间
const formatTime = (time: string) => {
  return new Date(time).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化日期
const formatDate = (date: Date) => {
  return date.toISOString().split('T')[0]
}

// 日期选择
const onDateSelect = (date: Date) => {
  selectedDate.value = date
  loadEvaluations()
}

// 加载评价记录
const loadEvaluations = async () => {
  const dateStr = formatDate(selectedDate.value)
  
  try {
    const res = await http.get<any>('/evaluations/my-with-class-stats', {
      start_date: dateStr,
      end_date: dateStr
    })
    
    evaluations.value = res.my_records || []
    myChildName.value = res.my_child_name || ''
    myChildId.value = res.my_child_id || ''
    
    if (res.class_stats) {
      classStats.avg_rating = res.class_stats.avg_rating
      classStats.total_records = res.class_stats.total_records
      classStats.total_students = res.class_stats.total_students
    }
  } catch (error) {
    showFailToast('加载失败')
  } finally {
    refreshing.value = false
  }
}

// 加载本月统计
const loadMonthStats = async () => {
  const now = new Date()
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  
  try {
    const res = await http.get<any>('/evaluations/my-with-class-stats', {
      start_date: formatDate(startOfMonth),
      end_date: formatDate(now)
    })
    
    const records = res.my_records || []
    
    // 统计
    stats.total = records.length
    
    const uniqueDates = new Set<string>(records.map((e: any) => e.record_date))
    stats.days = uniqueDates.size
    evaluationDates.value = uniqueDates
    
    // 统计优秀评价（5星或高分）
    stats.excellent = records.filter((e: any) => {
      const value = parseFloat(e.value)
      return value >= 4 || value >= 80
    }).length
    
    // 更新班级统计
    if (res.class_stats) {
      classStats.avg_rating = res.class_stats.avg_rating
      classStats.total_records = res.class_stats.total_records
      classStats.total_students = res.class_stats.total_students
    }
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

// 统计
const stats = reactive({
  total: 0,
  days: 0,
  excellent: 0
})

// 初始化
onMounted(() => {
  loadEvaluations()
  loadMonthStats()
})
</script>

<style scoped lang="scss">
.evaluation-calendar {
  padding: 12px;
  padding-bottom: 60px;
  
  .dot-indicator {
    width: 6px;
    height: 6px;
    background: #3e7dc9;
    border-radius: 50%;
    margin: 2px auto;
  }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .evaluation-list {
    margin-bottom: 12px;
  }
  
  .stats-section {
    padding: 16px;
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      
      .stat-item {
        text-align: center;
        
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #3e7dc9;
        }
        
        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-top: 4px;
        }
      }
    }
  }
  
  .class-stats {
    margin-top: 12px;
  }
  
  .my-child-info {
    text-align: center;
    margin-top: 16px;
    padding: 8px;
  }
}
</style>
