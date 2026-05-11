<template>
  <div class="achievement-page">
    <van-nav-bar title="我的成就" />
    
    <!-- 成就总览 -->
    <div class="achievement-overview">
      <div class="total-count">
        <span class="number">{{ stats.total_achievements }}</span>
        <span class="label">已获得成就</span>
      </div>
      <div class="progress-ring">
        <van-circle 
          :current-rate="progressPercent" 
          :rate="progressPercent"
          :speed="100"
          :stroke-width="60"
          layer-color="#e8e8e8"
          color="#ffc107"
        >
          <template #default>
            <span class="progress-text">{{ stats.total_achievements }}/{{ stats.all_types.length }}</span>
          </template>
        </van-circle>
      </div>
    </div>
    
    <!-- 最近获得的成就 -->
    <div class="section" v-if="stats.recent_achievements.length > 0">
      <h3>最近获得</h3>
      <div class="recent-list">
        <div 
          v-for="achievement in stats.recent_achievements" 
          :key="achievement.id"
          class="achievement-card"
        >
          <div class="icon">{{ achievement.achievement_icon }}</div>
          <div class="info">
            <div class="name">{{ achievement.achievement_name }}</div>
            <div class="desc">{{ achievement.achievement_description }}</div>
            <div class="time">{{ formatTime(achievement.earned_at) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 所有成就 -->
    <div class="section">
      <h3>成就图鉴</h3>
      <van-tabs v-model:active="activeTab">
        <van-tab title="任务类">
          <div class="achievement-grid">
            <div 
              v-for="type in taskTypes" 
              :key="type.type"
              class="achievement-item"
              :class="{ earned: type.earned }"
            >
              <div class="icon">{{ type.icon }}</div>
              <div class="name">{{ type.name }}</div>
              <div class="desc">{{ type.description }}</div>
              <van-tag v-if="type.earned" type="success">已获得</van-tag>
              <van-tag v-else type="default">未解锁</van-tag>
            </div>
          </div>
        </van-tab>
        
        <van-tab title="坚持类">
          <div class="achievement-grid">
            <div 
              v-for="type in streakTypes" 
              :key="type.type"
              class="achievement-item"
              :class="{ earned: type.earned }"
            >
              <div class="icon">{{ type.icon }}</div>
              <div class="name">{{ type.name }}</div>
              <div class="desc">{{ type.description }}</div>
              <van-tag v-if="type.earned" type="success">已获得</van-tag>
              <van-tag v-else type="default">未解锁</van-tag>
            </div>
          </div>
        </van-tab>
        
        <van-tab title="评价类">
          <div class="achievement-grid">
            <div 
              v-for="type in evaluationTypes" 
              :key="type.type"
              class="achievement-item"
              :class="{ earned: type.earned }"
            >
              <div class="icon">{{ type.icon }}</div>
              <div class="name">{{ type.name }}</div>
              <div class="desc">{{ type.description }}</div>
              <van-tag v-if="type.earned" type="success">已获得</van-tag>
              <van-tag v-else type="default">未解锁</van-tag>
            </div>
          </div>
        </van-tab>
        
        <van-tab title="特殊类">
          <div class="achievement-grid">
            <div 
              v-for="type in specialTypes" 
              :key="type.type"
              class="achievement-item"
              :class="{ earned: type.earned }"
            >
              <div class="icon">{{ type.icon }}</div>
              <div class="name">{{ type.name }}</div>
              <div class="desc">{{ type.description }}</div>
              <van-tag v-if="type.earned" type="success">已获得</van-tag>
              <van-tag v-else type="default">未解锁</van-tag>
            </div>
          </div>
        </van-tab>
      </van-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { getStudentAchievements } from '@/api/achievements'
import type { AchievementStats } from '@/api/achievements'

const route = useRoute()
const studentId = route.params.studentId as string || localStorage.getItem('studentId') || ''

const stats = ref<AchievementStats>({
  total_achievements: 0,
  recent_achievements: [],
  all_types: []
})

const activeTab = ref(0)

// 进度百分比
const progressPercent = computed(() => {
  if (stats.value.all_types.length === 0) return 0
  return (stats.value.total_achievements / stats.value.all_types.length) * 100
})

// 任务类成就
const taskTypes = computed(() => {
  return stats.value.all_types.filter(t => 
    t.type.startsWith('task_')
  )
})

// 坚持类成就
const streakTypes = computed(() => {
  return stats.value.all_types.filter(t => 
    t.type.includes('streak')
  )
})

// 评价类成就
const evaluationTypes = computed(() => {
  return stats.value.all_types.filter(t => 
    t.type.includes('star') || t.type.includes('all_rounder')
  )
})

// 特殊类成就
const specialTypes = computed(() => {
  return stats.value.all_types.filter(t => 
    t.type.includes('annotation') || t.type.includes('example')
  )
})

// 加载数据
async function loadData() {
  try {
    const response = await getStudentAchievements(studentId)
    stats.value = response
  } catch (error) {
    showToast('加载失败')
  }
}

// 格式化时间
function formatTime(time: string) {
  return new Date(time).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.achievement-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.achievement-overview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
  color: #fff;
}

.total-count {
  text-align: center;
}

.total-count .number {
  display: block;
  font-size: 48px;
  font-weight: bold;
}

.total-count .label {
  font-size: 14px;
  opacity: 0.9;
}

.progress-ring {
  width: 100px;
  height: 100px;
}

.progress-text {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.section {
  margin: 16px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.section h3 {
  margin: 0;
  padding: 16px;
  font-size: 16px;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
}

.recent-list {
  padding: 12px;
}

.achievement-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 8px;
}

.achievement-card:last-child {
  margin-bottom: 0;
}

.achievement-card .icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 50%;
}

.achievement-card .info {
  flex: 1;
}

.achievement-card .name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.achievement-card .desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.achievement-card .time {
  font-size: 12px;
  color: #999;
}

.achievement-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 12px;
}

.achievement-item {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  opacity: 0.5;
}

.achievement-item.earned {
  opacity: 1;
  background: #fff9e6;
}

.achievement-item .icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.achievement-item .name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.achievement-item .desc {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
  line-height: 1.4;
}
</style>
