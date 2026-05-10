<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">成长印记</h1>
      <p class="subtitle">家校协同分层自主学习与过程评价系统</p>
      
      <van-form @submit="handleLogin">
        <van-cell-group inset>
          <van-field
            v-model="form.phone"
            name="phone"
            label="手机号"
            placeholder="请输入手机号"
            type="tel"
            maxlength="11"
            :rules="[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
            ]"
          />
          <van-field
            v-model="form.password"
            name="password"
            label="密码"
            placeholder="请输入密码"
            type="password"
            :rules="[{ required: true, message: '请输入密码' }]"
          />
        </van-cell-group>
        
        <div class="actions">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            登录
          </van-button>
          <router-link to="/register" class="register-link">
            还没有账号？立即注册
          </router-link>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { authApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const form = reactive({
  phone: '',
  password: ''
})

async function handleLogin() {
  loading.value = true
  
  try {
    const res = await authApi.login(form)
    
    // 保存认证信息
    userStore.setTokens(res.access_token, res.refresh_token)
    userStore.setUser(res.user)
    
    showToast('登录成功')
    
    // 根据角色跳转
    const redirect = route.query.redirect as string
    if (redirect) {
      router.push(redirect)
    } else if (res.user.role === 'parent') {
      router.push('/parent')
    } else {
      router.push('/teacher')
    }
  } catch (error: any) {
    const message = error.response?.data?.detail || '登录失败，请重试'
    showToast(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.title {
  text-align: center;
  font-size: 28px;
  color: #303133;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  font-size: 14px;
  color: #909399;
  margin-bottom: 32px;
}

.actions {
  margin-top: 24px;
  
  .register-link {
    display: block;
    text-align: center;
    margin-top: 16px;
    color: #409eff;
    font-size: 14px;
  }
}
</style>
