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
          <el-menu-item-group title="班级管理">
            <el-menu-item index="/teacher/classes">
              <el-icon><School /></el-icon>
              <span>我的班级</span>
            </el-menu-item>
          </el-menu-item-group>
          
          <!-- 学习任务子菜单 -->
          <el-sub-menu index="task-menu">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>📝 学习任务</span>
            </template>
            <el-menu-item index="/teacher/tasks">
              <el-icon><List /></el-icon>
              <span>任务列表</span>
            </el-menu-item>
            <el-menu-item index="/teacher/tasks/create">
              <el-icon><Plus /></el-icon>
              <span>新建任务</span>
            </el-menu-item>
            <el-menu-item index="/teacher/tasks/submissions">
              <el-icon><View /></el-icon>
              <span>提交查看</span>
            </el-menu-item>
            <el-menu-item index="/teacher/tasks/stats">
              <el-icon><DataAnalysis /></el-icon>
              <span>任务统计</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 日常评价子菜单 -->
          <el-sub-menu index="evaluation-menu">
            <template #title>
              <el-icon><Star /></el-icon>
              <span>⭐ 日常评价</span>
            </template>
            <el-menu-item index="/teacher/evaluations">
              <el-icon><EditPen /></el-icon>
              <span>评价录入</span>
            </el-menu-item>
            <el-menu-item index="/teacher/evaluations/records">
              <el-icon><Tickets /></el-icon>
              <span>评价记录</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 数据报告 -->
          <el-menu-item-group title="数据报告">
            <el-menu-item index="/teacher/reports">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据分析</span>
            </el-menu-item>
            <el-menu-item index="/teacher/achievements">
              <el-icon><Trophy /></el-icon>
              <span>学生成就</span>
            </el-menu-item>
          </el-menu-item-group>
          
          <el-menu-item-group title="系统消息">
            <el-menu-item index="/teacher/messages">
              <el-icon><Bell /></el-icon>
              <span>消息中心</span>
            </el-menu-item>
          </el-menu-item-group>
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
  overflow-y: auto;
  
  .el-menu {
    border-right: none;
  }
}

.main {
  background: #f5f7fa;
  padding: 20px;
}
</style>
