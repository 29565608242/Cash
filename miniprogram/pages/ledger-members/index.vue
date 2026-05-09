<template>
  <view class="page-wrap">
    <view class="card">
      <view class="text-muted">账本ID：{{ ledgerId }}</view>
      <input class="input" v-model="draft.username" placeholder="要添加的用户名" />
      <picker mode="selector" :range="roles" :value="roleIndex" @change="onRoleChange">
        <view class="input">成员角色：{{ roles[roleIndex] }}</view>
      </picker>
      <view class="btn-primary" @tap="addMember">添加成员</view>
    </view>

    <view class="card">
      <view class="row list-item" v-for="item in members" :key="item.user_id">
        <view>
          <view>{{ item.username }}</view>
          <view class="text-muted">{{ item.role }}</view>
        </view>
        <view class="actions">
          <view class="btn-line" @tap="changeRole(item)">改角色</view>
          <view class="btn-line" @tap="removeMember(item)">移除</view>
        </view>
      </view>
      <view v-if="!members.length" class="text-muted">暂无成员</view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { api } from '../../services/api'
import { confirmModal, showError } from '../../services/utils'

const ledgerId = ref('')
const members = ref([])
const roles = ['viewer', 'editor', 'manager']
const roleIndex = ref(0)
const draft = reactive({
  username: '',
  role: 'viewer',
})

function onRoleChange(e) {
  roleIndex.value = Number(e.detail.value || 0)
  draft.role = roles[roleIndex.value]
}

onLoad((options) => {
  ledgerId.value = options.ledger_id || ''
})

async function loadMembers() {
  if (!ledgerId.value) return
  try {
    const res = await api.get(`/api/ledgers/${ledgerId.value}/members`)
    const list = []
    if (res.owner) {
      list.push({
        user_id: res.owner.user_id,
        username: `${res.owner.username}(所有者)`,
        role: res.owner.role,
      })
    }
    members.value = list.concat(res.members || [])
  } catch (error) {
    showError(error, '加载成员失败')
  }
}

async function addMember() {
  if (!draft.username.trim()) return uni.showToast({ title: '请输入用户名', icon: 'none' })
  try {
    await api.post(`/api/ledgers/${ledgerId.value}/members`, {
      username: draft.username.trim(),
      role: draft.role,
    })
    draft.username = ''
    await loadMembers()
  } catch (error) {
    showError(error, '添加成员失败')
  }
}

async function changeRole(item) {
  if (item.role === 'owner') return
  const idx = roles.indexOf(item.role)
  const nextRole = roles[(idx + 1) % roles.length]
  try {
    await api.put(`/api/ledgers/${ledgerId.value}/members/${item.user_id}`, { role: nextRole })
    await loadMembers()
  } catch (error) {
    showError(error, '更新角色失败')
  }
}

async function removeMember(item) {
  if (item.role === 'owner') return
  const ok = await confirmModal(`确认移除成员 ${item.username}？`)
  if (!ok) return
  try {
    await api.del(`/api/ledgers/${ledgerId.value}/members/${item.user_id}`)
    await loadMembers()
  } catch (error) {
    showError(error, '移除失败')
  }
}

onShow(loadMembers)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
