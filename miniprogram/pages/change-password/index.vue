<template>
  <view class="page-wrap">
    <view class="card">
      <input class="input" v-model="oldPwd" type="password" placeholder="旧密码" />
      <input class="input" v-model="newPwd" type="password" placeholder="新密码（至少6位）" />
      <view class="btn-primary" @tap="submit">修改密码</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { api, endpoints } from '../../services/api'
import { showError } from '../../services/utils'

const oldPwd = ref('')
const newPwd = ref('')

async function submit() {
  if (!oldPwd.value || !newPwd.value) return uni.showToast({ title: '请输入完整信息', icon: 'none' })
  if (newPwd.value.length < 6) return uni.showToast({ title: '新密码至少6位', icon: 'none' })
  try {
    await api.post(endpoints.user.changePassword, {
      old_password: oldPwd.value,
      new_password: newPwd.value,
    })
    oldPwd.value = ''
    newPwd.value = ''
    uni.showToast({ title: '修改成功', icon: 'success' })
  } catch (error) {
    showError(error, '修改失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
