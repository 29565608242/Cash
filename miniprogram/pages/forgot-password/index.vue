<template>
  <view class="page-wrap">
    <view class="hero">
      <text class="title">忘记密码</text>
      <text class="subtitle">{{ verified ? '设置新的登录密码' : '用注册邮箱验证账号身份' }}</text>
    </view>

    <view class="card form">
      <view class="steps">
        <view :class="verified ? 'step done' : 'step active'">
          <text class="num">{{ verified ? '✓' : '1' }}</text>
          <text>验证身份</text>
        </view>
        <view class="line"></view>
        <view :class="verified ? 'step active' : 'step'">
          <text class="num">2</text>
          <text>重置密码</text>
        </view>
      </view>

      <view v-if="!verified">
        <input class="input" v-model="form.username" placeholder="用户名" />
        <input class="input" v-model="form.email" placeholder="注册邮箱" />
        <view class="btn-primary" @tap="verifyAccount">下一步</view>
      </view>

      <view v-else>
        <input class="input" v-model="form.newPassword" type="password" password="true" placeholder="新密码（至少6位）" />
        <input class="input" v-model="form.confirmPassword" type="password" password="true" placeholder="确认新密码" />
        <view class="hint">密码至少 6 位字符</view>
        <view class="btn-primary" @tap="resetPassword">重置密码</view>
      </view>

      <view class="btn-line back" @tap="goLogin">返回登录</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { api, endpoints } from '../../services/api'

const verified = ref(false)
const resetToken = ref('')
const form = reactive({
  username: '',
  email: '',
  newPassword: '',
  confirmPassword: '',
})

async function verifyAccount() {
  const username = form.username.trim()
  const email = form.email.trim()
  if (!username || !email) {
    uni.showToast({ title: '请输入用户名和注册邮箱', icon: 'none' })
    return
  }

  try {
    const res = await api.post(endpoints.auth.forgotPassword, { username, email }, false)
    resetToken.value = res.reset_token || ''
    verified.value = true
    uni.showToast({ title: '验证通过', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '验证失败', icon: 'none' })
  }
}

async function resetPassword() {
  if (!form.newPassword || !form.confirmPassword) {
    uni.showToast({ title: '请输入完整密码信息', icon: 'none' })
    return
  }
  if (form.newPassword.length < 6) {
    uni.showToast({ title: '新密码至少 6 位', icon: 'none' })
    return
  }
  if (form.newPassword !== form.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  try {
    await api.post(endpoints.auth.resetPassword, {
      reset_token: resetToken.value,
      new_password: form.newPassword,
      confirm_password: form.confirmPassword,
    }, false)
    uni.showToast({ title: '重置成功', icon: 'success' })
    setTimeout(goLogin, 700)
  } catch (error) {
    uni.showToast({ title: error.message || '重置失败', icon: 'none' })
  }
}

function goLogin() {
  uni.redirectTo({ url: '/pages/login/index' })
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.page-wrap {
  min-height: 100vh;
  padding: 48rpx 0;
  background: radial-gradient(circle at 20% -10%, #dbe5ff 0, transparent 45%), $bg-page;
}

.hero {
  margin: 40rpx 40rpx 20rpx;
}

.title {
  display: block;
  color: $text-primary;
  font-size: 48rpx;
  font-weight: 800;
}

.subtitle {
  display: block;
  margin-top: 8rpx;
  color: $text-secondary;
  font-size: 28rpx;
}

.form {
  margin-top: 24rpx;
}

.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  margin-bottom: 28rpx;
}

.step {
  display: flex;
  align-items: center;
  gap: 8rpx;
  color: $text-light;
  font-size: 24rpx;
}

.step.active {
  color: $primary;
  font-weight: 700;
}

.step.done {
  color: $income;
  font-weight: 700;
}

.num {
  width: 36rpx;
  height: 36rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #eef2f7;
  color: inherit;
  font-size: 22rpx;
  font-weight: 700;
}

.active .num {
  background: $primary;
  color: #fff;
}

.done .num {
  background: $income;
  color: #fff;
}

.line {
  width: 44rpx;
  height: 2rpx;
  background: $border;
}

.hint {
  margin: -4rpx 0 18rpx;
  color: $text-light;
  font-size: 24rpx;
}

.back {
  margin-top: 26rpx;
  text-align: center;
  font-weight: 600;
}
</style>
