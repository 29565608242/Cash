<template>
  <view class="page-wrap">
    <view class="card">
      <view class="section-title">{{ ledger.name || '账本成员' }}</view>
      <view class="text-muted">账本ID：{{ ledgerId }}</view>
      <view v-if="loaded && !shareEnabled" class="notice">个人模式不支持分享加入，只能自己使用。</view>
      <view v-else-if="loaded" class="invite-panel">
        <view v-if="activeInvite" class="invite-code">
          <text class="invite-label">邀请码</text>
          <text class="invite-value">{{ activeInvite.code }}</text>
        </view>
        <view class="invite-actions">
          <view v-if="canManage" class="btn-primary" @tap="createInviteCode">生成邀请码</view>
          <view v-if="activeInvite" class="btn-line" @tap="copyInviteCode()">复制邀请码</view>
        </view>
        <view v-if="!canManage" class="text-muted">当前账号没有生成邀请码权限。</view>
      </view>
    </view>

    <view v-if="shareEnabled && canManage" class="card">
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
        <view v-if="shareEnabled && canManage && item.role !== 'owner'" class="actions">
          <view class="btn-line" @tap="changeRole(item)">改角色</view>
          <view class="btn-line" @tap="removeMember(item)">移除</view>
        </view>
      </view>
      <view v-if="!members.length" class="text-muted">暂无成员</view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, reactive } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { api } from '../../services/api'
import { confirmModal, showError } from '../../services/utils'

const ledgerId = ref('')
const ledger = ref({})
const members = ref([])
const inviteCodes = ref([])
const loaded = ref(false)
const roles = ['viewer', 'editor', 'manager']
const roleIndex = ref(1)
const draft = reactive({
  username: '',
  role: 'editor',
})

const shareEnabled = computed(() => Boolean(ledger.value.id) && ledger.value.share_enabled !== false && !ledger.value.is_personal)
const canManage = computed(() => ledger.value.role === 'manager' || ledger.value.role === 'owner')
const activeInvite = computed(() =>
  inviteCodes.value.find((item) => item.is_active) || inviteCodes.value[0] || null
)

function onRoleChange(e) {
  roleIndex.value = Number(e.detail.value || 0)
  draft.role = roles[roleIndex.value]
}

onLoad((options) => {
  ledgerId.value = options.ledger_id || ''
})

async function ensureLedgerId() {
  if (ledgerId.value) return true
  const res = await api.get('/api/miniapp/dashboard')
  const payload = res.data || {}
  ledgerId.value = payload.current_ledger_id || ''
  return Boolean(ledgerId.value)
}

function pushMember(list, seen, member) {
  if (!member || !member.user_id || seen.has(member.user_id)) return
  seen.add(member.user_id)
  list.push({
    user_id: member.user_id,
    username: member.role === 'owner' ? `${member.username}(所有者)` : member.username,
    role: member.role,
  })
}

async function loadInviteCodes() {
  inviteCodes.value = []
  if (!ledgerId.value || !shareEnabled.value) return
  const res = await api.get(`/api/ledgers/${ledgerId.value}/invite-codes`)
  inviteCodes.value = res.invite_codes || []
}

async function loadMembers() {
  try {
    const ok = await ensureLedgerId()
    if (!ok) return
    const res = await api.get(`/api/ledgers/${ledgerId.value}/members`)
    ledger.value = res.ledger || {}
    loaded.value = true
    const list = []
    const seen = new Set()
    if (res.owner) {
      pushMember(list, seen, res.owner)
    }
    ;(res.members || []).forEach((item) => pushMember(list, seen, item))
    members.value = list
    await loadInviteCodes()
  } catch (error) {
    showError(error, '加载成员失败')
  }
}

async function addMember() {
  if (!shareEnabled.value) return uni.showToast({ title: '个人模式不支持添加成员', icon: 'none' })
  if (!canManage.value) return uni.showToast({ title: '没有成员管理权限', icon: 'none' })
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

async function createInviteCode() {
  if (!shareEnabled.value) return uni.showToast({ title: '个人模式不支持分享加入', icon: 'none' })
  if (!canManage.value) return uni.showToast({ title: '没有邀请权限', icon: 'none' })
  try {
    const res = await api.post(`/api/ledgers/${ledgerId.value}/invite-codes`, {
      max_uses: 0,
      expires_in_hours: 0,
    })
    if (res.invite_code) {
      inviteCodes.value = [res.invite_code, ...inviteCodes.value]
      copyInviteCode(res.invite_code.code)
    }
  } catch (error) {
    showError(error, '生成邀请码失败')
  }
}

function copyInviteCode(code = '') {
  const value = code || (activeInvite.value && activeInvite.value.code)
  if (!value) return uni.showToast({ title: '暂无邀请码', icon: 'none' })
  uni.setClipboardData({
    data: value,
    success: () => uni.showToast({ title: '邀请码已复制', icon: 'success' }),
  })
}

async function changeRole(item) {
  if (!shareEnabled.value || !canManage.value || item.role === 'owner') return
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
  if (!shareEnabled.value || !canManage.value || item.role === 'owner') return
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

.section-title {
  margin-bottom: 10rpx;
  color: $text-primary;
  font-size: 34rpx;
  font-weight: 800;
}

.notice {
  margin-top: 18rpx;
  padding: 20rpx;
  border-radius: 12rpx;
  color: #7f5b16;
  background: #fff7df;
  font-size: 26rpx;
}

.invite-panel {
  margin-top: 20rpx;
}

.invite-code {
  padding: 20rpx;
  border-radius: 12rpx;
  background: #f5fbff;
  border: 1px solid #dbeff7;
}

.invite-label {
  display: block;
  color: $text-secondary;
  font-size: 24rpx;
}

.invite-value {
  display: block;
  margin-top: 8rpx;
  color: #0f3c5c;
  font-size: 34rpx;
  font-weight: 800;
  word-break: break-all;
}

.invite-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
  margin-top: 18rpx;
}
</style>
