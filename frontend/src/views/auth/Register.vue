<template>
  <div class="register-container">
    <div class="register-box">
      <h1 class="title">注册账号</h1>
      
      <van-form @submit="handleRegister">
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
            v-model="form.name"
            name="name"
            label="姓名"
            placeholder="请输入姓名"
            :rules="[{ required: true, message: '请输入姓名' }]"
          />
          <van-field
            v-model="form.password"
            name="password"
            label="密码"
            placeholder="请输入密码（至少6位）"
            type="password"
            :rules="[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' }
            ]"
          />
          <van-field name="role" label="身份">
            <template #input>
              <van-radio-group v-model="form.role" direction="horizontal">
                <van-radio name="teacher">教师</van-radio>
                <van-radio name="parent">家长</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <van-field
            v-model="form.verification_code"
            name="code"
            label="验证码"
            placeholder="请输入验证码"
            maxlength="6"
            :rules="[{ required: true, message: '请输入验证码' }]"
          >
            <template #button>
              <van-button 
                size="small" 
                type="primary" 
                :disabled="countdown > 0"
                @click="sendCode"
              >
                {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
              </van-button>
            </template>
          </van-field>
        </van-cell-group>
        
        <div class="actions">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            注册
          </van-button>
          <router-link to="/login" class="login-link">
            已有账号？立即登录
          </router-link>
        </div>
      </van-form>
      
      <div class="test-hint">
        <p>测试环境验证码固定为：<strong>123456</strong></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { authApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const countdown = ref(0)
const form = reactive({
  phone: '',
  name: '',
  password: '',
  role: 'teacher' as 'teacher' | 'parent',
  verification_code: ''
})

async function sendCode() {
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    showToast('请输入正确的手机号')
    return
  }
  
  try {
    const res = await authApi.sendCode(form.phone)
    showToast(res.message)
    
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    showToast('发送失败，请重试')
  }
}

async function handleRegister() {
  loading.value = true
  
  try {
    const res = await authApi.register({
      phone: form.phone,
      name: form.name,
      password: form.password,
      role: form.role,
      verification_code: form.verification_code
    })
    
    // 保存认证信息
    userStore.setTokens(res.access_token, res.refresh_token)
    userStore.setUser(res.user)
    
    showToast('注册成功')
    
    // 根据角色跳转
    if (res.user.role === 'parent') {
      router.push('/parent')
    } else {
      router.push('/teacher')
    }
  } catch (error: any) {
    const message = error.response?.data?.detail || '注册失败，请重试'
    showToast(message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-box {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.title {
  text-align: center;
  font-size: 24px;
  color: #303133;
  margin-bottom: 24px;
}

.actions {
  margin-top: 24px;
  
  .login-link {
    display: block;
    text-align: center;
    margin-top: 16px;
    color: #409eff;
    font-size: 14px;
  }
}

.test-hint {
  margin-top: 24px;
  padding: 12px;
  background: #fff3cd;
  border-radius: 8px;
  font-size: 12px;
  color: #856404;
  text-align: center;
}
</style>
