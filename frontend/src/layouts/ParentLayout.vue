<template>
  <div class="parent-layout">
    <!-- 顶部导航 -->
    <van-nav-bar
      :title="pageTitle"
      left-arrow
      @click-left="goBack"
      v-if="showBack"
    />
    
    <!-- 主内容区 -->
    <div class="content">
      <router-view />
    </div>
    
    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" route>
      <van-tabbar-item to="/parent/tasks" icon="notes-o">
        学习建议
      </van-tabbar-item>
      <van-tabbar-item to="/parent/evaluations" icon="star-o">
        评价记录
      </van-tabbar-item>
      <van-tabbar-item to="/parent/growth" icon="chart-trending-o">
        成长档案
      </van-tabbar-item>
      <van-tabbar-item to="/parent/me" icon="user-o">
        我的
      </van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeTab = ref(0)

const pageTitle = computed(() => {
  const meta = route.meta.title as string
  return meta || '成长印记'
})

const showBack = computed(() => {
  return route.path !== '/parent/tasks'
})

function goBack() {
  router.back()
}
</script>

<style scoped lang="scss">
.parent-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.content {
  flex: 1;
  padding: 16px;
  padding-bottom: 60px;
}
</style>
