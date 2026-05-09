<template>
  <view class="page-wrap">
    <view class="card">
      <input class="input" v-model="form.username" placeholder="用户名" />
      <input class="input" v-model="form.email" placeholder="邮箱（可选）" />
      <input class="input" v-model="form.password" type="password" placeholder="密码（至少6位）" />
      <input class="input" v-model="form.confirm" type="password" placeholder="确认密码" />
      <view class="btn-primary" @tap="submit">注册并登录</view>
      <view class="btn-line" @tap="goLogin">去登录</view>
    </view>
  </view>
</template>

<script setup>
import { reactive } from 'vue'
import { register } from '../../services/auth'
import { showError } from '../../services/utils'

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm: '',
})

function goLogin() {
  uni.redirectTo({ url: '/pages/login/index' })
}

async function submit() {
  const username = form.username.trim()
  if (!username) return uni.showToast({ title: '请输入用户名', icon: 'none' })
  if (!form.password || form.password.length < 6) return uni.showToast({ title: '密码至少6位', icon: 'none' })
  if (form.password !== form.confirm) return uni.showToast({ title: '两次密码不一致', icon: 'none' })
  try {
    await register(username, form.password, form.email.trim())
    uni.showToast({ title: '注册成功', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/index/index' }), 300)
  } catch (error) {
    showError(error, '注册失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.btn-line {
  text-align: center;
  margin-top: 20rpx;
}
</style>
