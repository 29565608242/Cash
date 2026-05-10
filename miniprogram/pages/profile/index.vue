<template>
  <view class="page">
    <view class="card user">
      <view class="avatar-wrap" @tap="changeAvatar">
        <image v-if="form.avatar && form.avatar !== 'default_avatar.svg'" class="avatar-img" :src="form.avatar" mode="aspectFill" />
        <view v-else class="avatar">{{ userInitial }}</view>
        <view class="avatar-overlay">更换</view>
      </view>
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
  avatar: '',
})

const password = reactive({
  old_password: '',
  new_password: '',
})

const userInitial = computed(() => (form.username || 'U').charAt(0).toUpperCase())

async function changeAvatar() {
  uni.chooseImage({
    count: 1,
    success: async (res) => {
      const tempPath = res.tempFilePaths[0]
      uni.showLoading({ title: '上传中...' })
      try {
        const uploadRes = await uni.uploadFile({
          url: 'http://127.0.0.1:8080/api/miniapp/upload',
          filePath: tempPath,
          name: 'file',
          header: { Authorization: 'Bearer ' + store.state.token }
        })
        uni.hideLoading()
        const data = JSON.parse(uploadRes.data || '{}')
        if (data.file && data.file.url) {
          const avatarUrl = 'http://127.0.0.1:8080/static/avatars/' + data.file.name
          form.avatar = avatarUrl
          await api.put('/api/user/profile', { avatar: data.file.name })
          uni.showToast({ title: '头像已更新', icon: 'success' })
        } else {
          uni.showToast({ title: data.message || '上传失败', icon: 'none' })
        }
      } catch (error) {
        uni.hideLoading()
        uni.showToast({ title: '上传失败', icon: 'none' })
      }
    }
  })
}

async function loadProfile() {
  try {
    const res = await api.get('/api/user/profile')
    const user = res.user || {}
    form.username = user.username || ''
    form.nickname = user.nickname || ''
    form.email = user.email || ''
    form.phone = user.phone || ''
    form.avatar = user.avatar || ''
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

.avatar-wrap {
  position: relative;
  width: 90rpx;
  height: 90rpx;
  flex-shrink: 0;
}

.avatar-img {
  width: 90rpx;
  height: 90rpx;
  border-radius: 45rpx;
  background: #f0f2f5;
}

.avatar {
  width: 90rpx;
  height: 90rpx;
  border-radius: 45rpx;
  background: linear-gradient(135deg, #5770f2 0%, #3551d0 100%);
  color: #fff;
  text-align: center;
  line-height: 90rpx;
  font-size: 36rpx;
  font-weight: 700;
}

.avatar-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 18rpx;
  text-align: center;
  line-height: 28rpx;
  border-radius: 0 0 45rpx 45rpx;
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
