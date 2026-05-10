<template>
  <el-container class="teacher-layout">
    <el-header class="header">
      <div class="logo">成长印记</div>
      <div class="user-info">
        <span>{{ userStore.user?.name }}</span>
        <el-dropdown @command="handleCommand">
          <el-avatar :size="32" icon="User" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    
    <el-container>
      <el-aside width="200px" class="aside">
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/teacher/classes">
            <el-icon><School /></el-icon>
            <span>我的班级</span>
          </el-menu-item>
          <el-menu-item index="/teacher/tasks">
            <el-icon><Document /></el-icon>
            <span>学习任务</span>
          </el-menu-item>
          <el-menu-item index="/teacher/evaluations">
            <el-icon><Star /></el-icon>
            <span>日常评价</span>
          </el-menu-item>
          <el-menu-item index="/teacher/reports">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据分析</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

function handleCommand(command: string) {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped lang="scss">
.teacher-layout {
  height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  
  .logo {
    font-size: 20px;
    font-weight: 600;
    color: #409eff;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    span {
      color: #606266;
    }
  }
}

.aside {
  background: #304156;
  
  .el-menu {
    border-right: none;
  }
}

.main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
