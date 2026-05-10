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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { showFailToast } from 'vant'
import { getMyEvaluations } from '@/api/evaluations'
import type { EvaluationRecord, EvaluationDimension } from '@/api/types'

const route = useRoute()

// 状态
const refreshing = ref(false)
const selectedDate = ref(new Date())
const evaluations = ref<EvaluationRecord[]>([])
const dimensions = ref<EvaluationDimension[]>([])
const evaluationDates = ref<Set<string>>(new Set())

// 统计
const stats = reactive({
  total: 0,
  days: 0,
  excellent: 0
})

// 日期范围
const minDate = new Date(2024, 0, 1)
const maxDate = new Date()

// 选中日期标签
const selectedDateLabel = computed(() => {
  const d = selectedDate.value
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

// 学生ID（从用户信息获取）
const studentId = computed(() => {
  // TODO: 从store或路由获取实际学生ID
  return route.query.student_id as string || ''
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
  if (!studentId.value) return
  
  const dateStr = formatDate(selectedDate.value)
  
  try {
    const res = await getMyEvaluations({
      student_id: studentId.value,
      start_date: dateStr,
      end_date: dateStr
    })
    evaluations.value = res
  } catch (error) {
    showFailToast('加载失败')
  } finally {
    refreshing.value = false
  }
}

// 加载本月统计
const loadMonthStats = async () => {
  if (!studentId.value) return
  
  const now = new Date()
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  
  try {
    const res = await getMyEvaluations({
      student_id: studentId.value,
      start_date: formatDate(startOfMonth),
      end_date: formatDate(now)
    })
    
    // 统计
    stats.total = res.length
    
    const uniqueDates = new Set(res.map(e => e.record_date))
    stats.days = uniqueDates.size
    evaluationDates.value = uniqueDates
    
    // 统计优秀评价（5星或高分）
    stats.excellent = res.filter(e => {
      const value = parseFloat(e.value)
      return value >= 4 || value >= 80
    }).length
  } catch (error) {
    console.error('加载统计失败', error)
  }
}

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
}
</style>
