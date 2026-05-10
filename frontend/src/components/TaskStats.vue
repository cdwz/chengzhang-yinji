<template>
  <div class="task-stats">
    <van-cell-group inset class="stats-overview">
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总任务数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.submitted }}</div>
          <div class="stat-label">已提交</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待完成</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.completionRate }}%</div>
          <div class="stat-label">完成率</div>
        </div>
      </div>
    </van-cell-group>

    <div class="section-title">各科目统计</div>
    <van-cell-group inset>
      <van-cell
        v-for="item in stats.bySubject"
        :key="item.subject"
        :title="item.subject"
        :value="`${item.count}个任务`"
        :label="`完成率: ${item.completionRate}%`"
      />
    </van-cell-group>

    <div class="section-title">最近一周趋势</div>
    <van-cell-group inset>
      <div class="chart-container">
        <div class="chart-bars">
          <div
            v-for="(day, index) in stats.weeklyTrend"
            :key="index"
            class="chart-bar-wrapper"
          >
            <div class="chart-bar" :style="{ height: `${day.percentage}%` }">
              <span class="bar-value">{{ day.count }}</span>
            </div>
            <div class="bar-label">{{ day.label }}</div>
          </div>
        </div>
      </div>
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface TaskStats {
  total: number
  submitted: number
  pending: number
  completionRate: number
  bySubject: Array<{
    subject: string
    count: number
    completionRate: number
  }>
  weeklyTrend: Array<{
    label: string
    count: number
    percentage: number
  }>
}

defineProps<{
  classId?: string
}>()

const stats = ref<TaskStats>({
  total: 0,
  submitted: 0,
  pending: 0,
  completionRate: 0,
  bySubject: [],
  weeklyTrend: []
})

// 生成最近一周数据
const generateWeeklyTrend = () => {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const today = new Date().getDay()
  const result = []
  
  for (let i = 0; i < 7; i++) {
    const dayIndex = (today - 6 + i + 7) % 7
    result.push({
      label: days[dayIndex === 0 ? 6 : dayIndex - 1],
      count: Math.floor(Math.random() * 5),
      percentage: Math.floor(Math.random() * 100)
    })
  }
  
  return result
}

// 加载统计数据
const loadStats = async () => {
  // TODO: 调用后端API获取真实数据
  // 模拟数据
  stats.value = {
    total: 24,
    submitted: 18,
    pending: 6,
    completionRate: 75,
    bySubject: [
      { subject: '语文', count: 8, completionRate: 80 },
      { subject: '数学', count: 6, completionRate: 75 },
      { subject: '英语', count: 5, completionRate: 70 },
      { subject: '科学', count: 5, completionRate: 65 }
    ],
    weeklyTrend: generateWeeklyTrend()
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.task-stats {
  .stats-overview {
    padding: 16px;
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
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
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .chart-container {
    padding: 16px;
    
    .chart-bars {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      height: 150px;
      padding-top: 20px;
      
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
  }
}
</style>
