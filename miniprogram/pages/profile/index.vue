<template>
  <view class="page">
    <view class="card user">
      <view class="avatar">{{ userInitial }}</view>
      <view class="meta">
        <text class="name">{{ form.username || '-' }}</text>
        <text class="muted">{{ form.email || '未设置邮箱' }}</text>
      </view>
    </view>

    <view class="card">
      <input class="input" v-model="form.nickname" placeholder="昵称" />
      <input class="input" v-model="form.email" placeholder="邮箱" />
      <input class="input" v-model="form.phone" placeholder="手机号" />
      <view class="btn-primary" @tap="saveProfile">保存资料</view>
    </view>

    <view class="card">
      <input class="input" v-model="password.old_password" type="password" placeholder="旧密码" />
      <input class="input" v-model="password.new_password" type="password" placeholder="新密码（至少6位）" />
      <view class="btn-primary" @tap="changePassword">修改密码</view>
    </view>

    <view class="card logout" @tap="doLogout">退出登录</view>
  </view>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../services/api'
import { logout } from '../../services/auth'
import { store } from '../../store/index'

const form = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
})

const password = reactive({
  old_password: '',
  new_password: '',
})

const userInitial = computed(() => (form.username || 'U').charAt(0).toUpperCase())

async function loadProfile() {
  try {
    const res = await api.get('/api/user/profile')
    const user = res.user || {}
    form.username = user.username || ''
    form.nickname = user.nickname || ''
    form.email = user.email || ''
    form.phone = user.phone || ''
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

async function saveProfile() {
  try {
    await api.put('/api/user/profile', {
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
    })
    store.state.user = { ...(store.state.user || {}), ...form }
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  }
}

async function changePassword() {
  if (!password.old_password || !password.new_password) {
    uni.showToast({ title: '请输入完整密码信息', icon: 'none' })
    return
  }
  if (password.new_password.length < 6) {
    uni.showToast({ title: '新密码至少6位', icon: 'none' })
    return
  }
  try {
    await api.post('/api/user/change-password', password)
    password.old_password = ''
    password.new_password = ''
    uni.showToast({ title: '密码修改成功', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '修改失败', icon: 'none' })
  }
}

async function doLogout() {
  await logout()
  uni.reLaunch({ url: '/pages/login/index' })
}

onShow(() => {
  loadProfile()
})
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';

.page {
  padding: 12rpx 0 24rpx;
}

.user {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.avatar {
  width: 84rpx;
  height: 84rpx;
  border-radius: 42rpx;
  background: linear-gradient(135deg, #5770f2 0%, #3551d0 100%);
  color: #fff;
  text-align: center;
  line-height: 84rpx;
  font-size: 36rpx;
  font-weight: 700;
}

.meta {
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 32rpx;
  font-weight: 700;
}

.muted {
  color: $text-secondary;
  margin-top: 6rpx;
}

.input {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 0 22rpx;
  margin-bottom: 14rpx;
}

.logout {
  text-align: center;
  color: #fff;
  background: linear-gradient(135deg, #ef5353 0%, #d13a3a 100%);
  font-weight: 700;
}
</style>
