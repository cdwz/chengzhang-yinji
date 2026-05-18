<template>
  <div class="evaluation-calendar">
    <!-- 顶部标签卡 -->
    <van-tabs v-model:active="activeTab" sticky>
      <!-- 今日评价 -->
      <van-tab title="今日评价">
        <div class="tab-content">
          <div class="date-info">
            <van-icon name="calendar-o" />
            <span>{{ todayLabel }}</span>
            <van-tag v-if="isWeekend" type="warning" >周末</van-tag>
            <van-tag v-else-if="isHoliday" type="danger" >节假日</van-tag>
          </div>
          
          <van-loading v-if="loadingToday" size="24px" vertical>加载中...</van-loading>
          
          <div v-else-if="todayEvaluations.length > 0" class="evaluation-list">
            <van-cell-group inset>
              <van-cell
                v-for="record in todayEvaluations"
                :key="record.id"
                :title="getDimensionName(record.dimension_id)"
                :label="formatTime(record.updated_at)"
              >
                <template #value>
                  <van-rate v-if="getDimensionType(record.dimension_id) === 'star'" :model-value="Number(record.value)" readonly size="16" />
                  <van-tag v-else type="primary">{{ record.value }}</van-tag>
                </template>
              </van-cell>
            </van-cell-group>
          </div>
          
          <van-empty v-else description="暂无评价记录" image-size="80" />
        </div>
      </van-tab>
      
      <!-- 历史评价 -->
      <van-tab title="历史评价">
        <div class="tab-content">
          <!-- 日历组件 -->
          <van-calendar
            :show-title="false"
            :poppable="false"
            :show-confirm="false"
            :min-date="minDate"
            :max-date="maxDate"
            :default-date="defaultDate"
            :style="{ height: '300px' }"
            @select="onDateSelect"
            class="history-calendar"
          >
            <template #bottom-info="day">
              <div v-if="hasEvaluation(day.date)" class="dot-indicator"></div>
            </template>
          </van-calendar>
          
          <!-- 选中日期的评价记录 -->
          <div class="selected-section" v-if="selectedDate">
            <div class="section-header">
              <van-icon name="clock-o" />
              <span>{{ selectedDateLabel }}的评价</span>
            </div>
            
            <van-loading v-if="loadingSelected" size="24px" vertical>加载中...</van-loading>
            
            <div v-else-if="selectedEvaluations.length > 0" class="evaluation-list">
              <van-cell-group inset>
                <van-cell
                  v-for="record in selectedEvaluations"
                  :key="record.id"
                  :title="getDimensionName(record.dimension_id)"
                  :label="formatTime(record.updated_at)"
                >
                  <template #value>
                    <van-rate v-if="getDimensionType(record.dimension_id) === 'star'" :model-value="Number(record.value)" readonly size="16" />
                    <van-tag v-else type="primary">{{ record.value }}</van-tag>
                  </template>
                </van-cell>
              </van-cell-group>
            </div>
            
            <van-empty v-else description="当日暂无评价记录" image-size="60" />
          </div>
        </div>
      </van-tab>
    </van-tabs>
    
    <!-- 我的孩子信息 -->
    <div class="my-child-info" v-if="myChildName">
      <van-tag type="success">我的孩子：{{ myChildName }}</van-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showFailToast } from 'vant'
import { http } from '@/utils/request'
import type { EvaluationRecord, EvaluationDimension } from '@/api/types'

// 状态
const activeTab = ref(0)
const loadingToday = ref(true)
const loadingSelected = ref(false)
const todayEvaluations = ref<EvaluationRecord[]>([])
const selectedEvaluations = ref<EvaluationRecord[]>([])
const dimensions = ref<EvaluationDimension[]>([])
const evaluationDates = ref<Set<string>>(new Set())
const selectedDate = ref<Date | null>(null)
const myChildName = ref('')

// 日期
const today = new Date()
const minDate = new Date(today.getFullYear(), today.getMonth() - 6, 1)
const maxDate = today
const defaultDate = today

// 是否周末
const isWeekend = computed(() => {
  const day = today.getDay()
  return day === 0 || day === 6
})

// 是否节假日（简化处理，实际应查询节假日API）
const isHoliday = ref(false)

// 今日标签
const todayLabel = computed(() => {
  const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${today.getMonth() + 1}月${today.getDate()}日 ${weekDays[today.getDay()]}`
})

// 选中日期标签
const selectedDateLabel = computed(() => {
  if (!selectedDate.value) return ''
  const d = selectedDate.value
  return `${d.getMonth() + 1}月${d.getDate()}日`
})

// 格式化日期
const formatDate = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 格式化时间
const formatTime = (time: string) => {
  return new Date(time).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

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

// 获取维度类型
const getDimensionType = (dimensionId: string) => {
  const dim = dimensions.value.find(d => d.id === dimensionId)
  return dim?.type || 'star'
}

// 日期选择
const onDateSelect = (date: Date) => {
  selectedDate.value = date
  loadSelectedEvaluations()
}

// 加载今日评价
const loadTodayEvaluations = async () => {
  loadingToday.value = true
  
  // 如果是周末或节假日，查找最近一个上学日
  let queryDate = today
  if (isWeekend.value || isHoliday.value) {
    // 往前找最近的工作日
    queryDate = new Date(today)
    while (queryDate.getDay() === 0 || queryDate.getDay() === 6) {
      queryDate.setDate(queryDate.getDate() - 1)
    }
  }
  
  const dateStr = formatDate(queryDate)
  
  try {
    const res = await http.get<any>('/evaluations/my-with-class-stats', {
      start_date: dateStr,
      end_date: dateStr
    })
    
    todayEvaluations.value = res.my_records || []
    myChildName.value = res.my_child_name || ''
  } catch (error) {
    console.error('加载今日评价失败', error)
  } finally {
    loadingToday.value = false
  }
}

// 加载选中日期评价
const loadSelectedEvaluations = async () => {
  if (!selectedDate.value) return
  
  loadingSelected.value = true
  const dateStr = formatDate(selectedDate.value)
  
  try {
    const res = await http.get<any>('/evaluations/my-with-class-stats', {
      start_date: dateStr,
      end_date: dateStr
    })
    
    selectedEvaluations.value = res.my_records || []
  } catch (error) {
    showFailToast('加载失败')
  } finally {
    loadingSelected.value = false
  }
}

// 加载评价维度
const loadDimensions = async () => {
  try {
    const res = await http.get<EvaluationDimension[]>('/evaluations/dimensions')
    dimensions.value = res
  } catch (error) {
    console.error('加载维度失败', error)
  }
}

// 加载历史评价日期
const loadEvaluationDates = async () => {
  const startStr = formatDate(minDate)
  const endStr = formatDate(today)
  
  try {
    const res = await http.get<any>('/evaluations/my-with-class-stats', {
      start_date: startStr,
      end_date: endStr
    })
    
    const records = res.my_records || []
    const dates = new Set<string>()
    records.forEach((e: any) => {
      if (e.record_date) {
        dates.add(e.record_date)
      }
    })
    
    evaluationDates.value = dates
  } catch (error) {
    console.error('加载历史评价失败', error)
  }
}

// 初始化
onMounted(async () => {
  await loadDimensions()
  await Promise.all([
    loadTodayEvaluations(),
    loadEvaluationDates()
  ])
})
</script>

<style scoped lang="scss">
.evaluation-calendar {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 70px;
  
  :deep(.van-tabs__wrap) {
    background: #fff;
  }
  
  .tab-content {
    padding: 12px;
  }
  
  .date-info {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: #fff;
    border-radius: 8px;
    margin-bottom: 12px;
    font-size: 15px;
    
    .van-icon {
      color: #1677ff;
    }
  }
  
  .history-calendar {
    border-radius: 8px;
    overflow: hidden;
  }
  
  .selected-section {
    margin-top: 12px;
    
    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 0;
      font-size: 15px;
      font-weight: 500;
      color: #333;
      
      .van-icon {
        color: #1677ff;
      }
    }
  }
  
  .dot-indicator {
    width: 6px;
    height: 6px;
    background: #1677ff;
    border-radius: 50%;
    margin: 2px auto 0;
  }
  
  .evaluation-list {
    margin-top: 8px;
  }
  
  .my-child-info {
    position: fixed;
    bottom: 60px;
    left: 0;
    right: 0;
    display: flex;
    justify-content: center;
    padding: 8px;
    background: rgba(255, 255, 255, 0.95);
    border-top: 1px solid #eee;
  }
}
</style>
