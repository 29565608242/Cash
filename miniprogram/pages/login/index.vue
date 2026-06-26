<template>
  <view class="page">
    <view class="hero">
      <text class="title">线上记账</text>
      <text class="subtitle">移动端快速记账与账本协作</text>
    </view>

    <view class="card form">
      <input class="input" v-model="username" placeholder="用户名" />
      <input class="input" v-model="password" type="password" password="true" placeholder="密码" />

      <view class="btn-primary" @tap="submitLogin">登录</view>
      <view class="auth-links">
        <text @tap="goForgotPassword">忘记密码</text>
        <text class="divider">|</text>
        <text @tap="goAccountPassword">修改账号密码</text>
      </view>
      <view class="btn-ghost" @tap="goRegister">去注册</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { login } from '../../services/auth'

const username = ref('')
const password = ref('')

function validate() {
  if (!username.value.trim() || !password.value) {
    uni.showToast({ title: '请输入用户名和密码', icon: 'none' })
    return false
  }
  if (password.value.length < 6) {
    uni.showToast({ title: '密码至少 6 位', icon: 'none' })
    return false
  }
  return true
}

async function submitLogin() {
  if (!validate()) return
  try {
    await login(username.value.trim(), password.value)
    uni.switchTab({ url: '/pages/ledgers/index' })
  } catch (error) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
  }
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/index' })
}

function goForgotPassword() {
  uni.navigateTo({ url: '/pages/forgot-password/index' })
}

function goAccountPassword() {
  uni.navigateTo({ url: '/pages/account-password/index' })
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.page {
  min-height: 100vh;
  padding: 48rpx 0;
  background: radial-gradient(circle at 20% -10%, #dbe5ff 0, transparent 45%), $bg-page;
}

.hero {
  margin: 40rpx 40rpx 12rpx;
}

.title {
  display: block;
  font-size: 52rpx;
  font-weight: 700;
  color: $text-primary;
}

.subtitle {
  display: block;
  margin-top: 8rpx;
  color: $text-secondary;
}

.form {
  margin-top: 24rpx;
}

.input {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 0 22rpx;
  background: #fff;
  margin-bottom: 16rpx;
}

.btn-primary {
  margin-top: 8rpx;
}

.auth-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
  margin-top: 22rpx;
  color: $primary;
  font-size: 28rpx;
  font-weight: 600;
}

.divider {
  color: $text-light;
  font-weight: 400;
}

.btn-ghost {
  text-align: center;
  color: $primary;
  margin-top: 24rpx;
  font-weight: 600;
}
</style>
