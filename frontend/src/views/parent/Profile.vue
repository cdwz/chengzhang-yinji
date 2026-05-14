<template>
  <div class="parent-profile">
    <van-cell-group inset>
      <van-cell title="姓名" :value="user?.name" />
      <van-cell title="手机号" :value="user?.phone" />
    </van-cell-group>
    
    <van-cell-group inset style="margin-top: 12px;" v-if="students.length > 0">
      <van-cell title="绑定的学生">
        <template #value>
          <div v-for="s in students" :key="s.id" class="student-info">
            <span class="student-name">{{ s.name }}</span>
            <span class="student-class">（{{ s.class_name }}）</span>
          </div>
        </template>
      </van-cell>
    </van-cell-group>
    
    <van-cell-group inset style="margin-top: 12px;" v-else>
      <van-cell title="绑定的学生" value="未绑定" />
    </van-cell-group>
    
    <div class="logout-btn">
      <van-button type="danger" block @click="logout">退出登录</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import { useUserStore } from '@/stores/user'
import { http } from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()
const user = ref(userStore.user)
const students = ref<any[]>([])

onMounted(async () => {
  try {
    const data = await http.get<any[]>('/students/my')
    students.value = data || []
  } catch (error) {
    console.error('加载学生列表失败', error)
  }
})

async function logout() {
  try {
    await showConfirmDialog({
      title: '提示',
      message: '确定要退出登录吗？'
    })
    userStore.logout()
    router.push('/login')
  } catch {
    // 取消
  }
}
</script>

<style scoped lang="scss">
.parent-profile {
  padding: 12px;
  padding-bottom: 80px;
  
  .student-info {
    text-align: right;
    .student-name {
      font-weight: 500;
    }
    .student-class {
      color: #909399;
      font-size: 12px;
      margin-left: 4px;
    }
  }
  
  .logout-btn {
    margin-top: 24px;
    padding: 0 12px;
  }
}
</style>
