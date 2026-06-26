<template>
  <view class="page-wrap">
    <view class="hero">
      <text class="title">修改账号密码</text>
      <text class="subtitle">输入当前密码后设置新密码</text>
    </view>

    <view class="card form">
      <input class="input" v-model="form.username" placeholder="用户名" />
      <input class="input" v-model="form.currentPassword" type="password" password="true" placeholder="当前密码" />
      <input class="input" v-model="form.newPassword" type="password" password="true" placeholder="新密码（至少6位）" />
      <input class="input" v-model="form.confirmPassword" type="password" password="true" placeholder="确认新密码" />
      <view class="hint">修改成功后请使用新密码重新登录</view>

      <view class="btn-primary" @tap="submit">保存新密码</view>
      <view class="btn-line back" @tap="goLogin">返回登录</view>
    </view>
  </view>
</template>

<script setup>
import { reactive } from 'vue'
import { api, endpoints } from '../../services/api'

const form = reactive({
  username: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

async function submit() {
  const username = form.username.trim()
  if (!username || !form.currentPassword || !form.newPassword || !form.confirmPassword) {
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
    await api.post(endpoints.auth.changePassword, {
      username,
      current_password: form.currentPassword,
      new_password: form.newPassword,
      confirm_password: form.confirmPassword,
    }, false)
    uni.showToast({ title: '修改成功', icon: 'success' })
    setTimeout(goLogin, 700)
  } catch (error) {
    uni.showToast({ title: error.message || '修改失败', icon: 'none' })
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
