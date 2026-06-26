<template>
  <view class="page-wrap ledger-page">
    <view class="hero-band">
      <view>
        <text class="hero-title">账本列表</text>
      </view>
      <view class="hero-actions">
        <view class="icon-btn" @tap="openJoin">入</view>
        <view class="icon-btn primary" @tap="openCreate">+</view>
      </view>
    </view>

    <view class="summary-strip">
      <view class="summary-item">
        <text class="summary-value">{{ ledgers.length }}</text>
        <text class="summary-label">账本</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">¥{{ formatMoney(totalBalance) }}</text>
        <text class="summary-label">总余额</text>
      </view>
      <view class="summary-item">
        <text class="summary-value">¥{{ formatMoney(monthExpense) }}</text>
        <text class="summary-label">本月支出</text>
      </view>
    </view>

    <view class="toolbar">
      <input class="search-input" v-model="keyword" placeholder="搜索账本" />
      <view class="sort-tabs">
        <view :class="sortMode === 'active' ? 'sort-tab active' : 'sort-tab'" @tap="sortMode = 'active'">当前</view>
        <view :class="sortMode === 'time' ? 'sort-tab active' : 'sort-tab'" @tap="sortMode = 'time'">时间</view>
      </view>
    </view>

    <view v-if="showCreatePanel" class="form-panel">
      <input class="form-input" v-model="draft.name" placeholder="新账本名称" />
      <input class="form-input" v-model="draft.description" placeholder="账本描述（可选）" />
      <view class="form-actions">
        <view class="plain-btn" @tap="showCreatePanel = false">取消</view>
        <view class="solid-btn" @tap="createLedger">创建账本</view>
      </view>
    </view>

    <view v-if="showJoinPanel" class="form-panel">
      <input class="form-input" v-model="inviteCode" placeholder="输入邀请码加入账本" />
      <view class="form-actions">
        <view class="plain-btn" @tap="showJoinPanel = false">取消</view>
        <view class="solid-btn" @tap="joinByCode">加入账本</view>
      </view>
    </view>

    <view :class="personalModeActive ? 'personal-mode-card active' : 'personal-mode-card'" @tap="selectPersonalMode">
      <view>
        <text class="share-tag">个人模式</text>
        <text class="ledger-name">个人记账</text>
        <text class="personal-mode-sub">只管理自己的数据，不参与成员分享</text>
      </view>
      <text class="current-tag" v-if="personalModeActive">当前</text>
    </view>

    <view class="ledger-list">
      <view
        v-for="item in filteredLedgers"
        :key="item.id"
        :class="item.is_current ? 'ledger-card current' : 'ledger-card'"
        @tap="selectLedger(item)"
      >
        <view class="card-bg"></view>
        <view class="ledger-top">
          <view>
            <text class="share-tag">{{ item.is_personal ? '个人' : '共享' }}</text>
            <text class="ledger-name">{{ item.name }}</text>
          </view>
          <text class="current-tag" v-if="item.is_current">当前</text>
        </view>

        <view class="member-row">
          <view class="avatars">
            <view v-for="member in visibleMembers(item)" :key="member.user_id" class="avatar">
              {{ avatarText(member) }}
            </view>
            <view v-if="item.share_enabled" class="avatar add" @tap.stop="goMembers(item.id)">+</view>
          </view>
          <text class="created">{{ formatCreatedAt(item.created_at) }} 创建</text>
        </view>

        <view class="ledger-footer">
          <view v-if="item.share_enabled" class="footer-action" @tap.stop="goMembers(item.id)">成员</view>
          <view class="footer-action" @tap.stop="goReports(item)">报表</view>
          <view v-if="item.role === 'manager'" class="footer-action danger" @tap.stop="removeLedger(item)">删除</view>
          <view class="balance-block">
            <text class="balance-label">账本余额</text>
            <text class="balance-value">¥{{ formatMoney(item.balance) }}</text>
          </view>
        </view>

        <view class="ledger-metrics">
          <text>本月收入 ¥{{ formatMoney(item.month_income) }}</text>
          <text>本月支出 ¥{{ formatMoney(item.month_expense) }}</text>
        </view>
      </view>
      <view v-if="!filteredLedgers.length" class="empty-state">
        <text class="empty-title">暂无共享账本</text>
        <text class="empty-sub">个人记账可直接使用个人模式</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, formatMoney, showError } from '../../services/utils'

const ledgers = ref([])
const personalModeActive = ref(true)
const keyword = ref('')
const sortMode = ref('active')
const showCreatePanel = ref(false)
const showJoinPanel = ref(false)
const inviteCode = ref('')
const draft = reactive({
  name: '',
  description: '',
})

const totalBalance = computed(() =>
  ledgers.value.reduce((sum, item) => sum + Number(item.balance || 0), 0)
)
const monthExpense = computed(() =>
  ledgers.value.reduce((sum, item) => sum + Number(item.month_expense || 0), 0)
)

const filteredLedgers = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  const list = ledgers.value.filter((item) => {
    if (!text) return true
    return `${item.name || ''} ${item.description || ''}`.toLowerCase().includes(text)
  })
  return [...list].sort((a, b) => {
    if (sortMode.value === 'active') {
      return Number(b.is_current) - Number(a.is_current) || Number(b.balance || 0) - Number(a.balance || 0)
    }
    return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
  })
})

async function loadLedgers() {
  try {
    const [ledgerRes, dashboardRes] = await Promise.all([
      api.get(endpoints.ledgers),
      api.get(endpoints.miniapp.dashboard),
    ])
    ledgers.value = ledgerRes.ledgers || []
    const dashboard = dashboardRes.data || {}
    personalModeActive.value = !dashboard.current_ledger_id
  } catch (error) {
    showError(error, '加载账本失败')
  }
}

async function selectPersonalMode() {
  try {
    await api.post(`${endpoints.ledgers}/personal`, {})
    personalModeActive.value = true
    ledgers.value = ledgers.value.map((ledger) => ({ ...ledger, is_current: false }))
    uni.switchTab({ url: '/pages/transaction-add/index' })
  } catch (error) {
    showError(error, '切换个人模式失败')
  }
}

function visibleMembers(item) {
  const members = item.members || []
  if (members.length) return members.slice(0, 3)
  return [{ user_id: item.owner_id, username: item.owner_name || item.name }]
}

function avatarText(member) {
  const name = member.nickname || member.username || '账'
  return name.slice(0, 1).toUpperCase()
}

function formatCreatedAt(value) {
  if (!value) return ''
  return value.slice(0, 10)
}

async function selectLedger(item) {
  try {
    await api.post(`${endpoints.ledgers}/${item.id}/switch`, {})
    ledgers.value = ledgers.value.map((ledger) => ({
      ...ledger,
      is_current: ledger.id === item.id,
    }))
    personalModeActive.value = false
    uni.switchTab({ url: '/pages/transaction-add/index' })
  } catch (error) {
    showError(error, '切换账本失败')
  }
}

function openCreate() {
  draft.name = ''
  draft.description = ''
  showJoinPanel.value = false
  showCreatePanel.value = true
}

async function createLedger() {
  const name = draft.name.trim()
  if (!name) {
    uni.showToast({ title: '请输入账本名称', icon: 'none' })
    return
  }
  try {
    await api.post(endpoints.ledgers, {
      name,
      description: draft.description.trim(),
      currency: 'CNY',
    })
    showCreatePanel.value = false
    await loadLedgers()
    uni.showToast({ title: '创建成功', icon: 'success' })
  } catch (error) {
    showError(error, '创建账本失败')
  }
}

function openJoin() {
  inviteCode.value = ''
  showCreatePanel.value = false
  showJoinPanel.value = true
}

async function joinByCode() {
  const code = inviteCode.value.trim()
  if (!code) {
    uni.showToast({ title: '请输入邀请码', icon: 'none' })
    return
  }
  try {
    await api.post('/api/ledgers/join', { code })
    showJoinPanel.value = false
    await loadLedgers()
    uni.showToast({ title: '加入成功', icon: 'success' })
  } catch (error) {
    showError(error, '加入失败')
  }
}

function goMembers(id) {
  uni.navigateTo({ url: `/pages/ledger-members/index?ledger_id=${id}` })
}

async function goReports(item) {
  try {
    await api.post(`${endpoints.ledgers}/${item.id}/switch`, {})
    uni.navigateTo({ url: '/pages/reports/index' })
  } catch (error) {
    showError(error, '打开报表失败')
  }
}

async function removeLedger(item) {
  if (item.role !== 'manager') {
    uni.showToast({ title: '仅管理员可删除', icon: 'none' })
    return
  }
  const ok = await confirmModal(`确认删除账本「${item.name}」？`)
  if (!ok) return
  try {
    await api.del(`${endpoints.ledgers}/${item.id}`)
    await loadLedgers()
  } catch (error) {
    showError(error, '删除账本失败')
  }
}

onShow(loadLedgers)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.ledger-page {
  min-height: 100vh;
  background: #f3f6f8;
  padding-bottom: 36rpx;
}

.hero-band {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 30rpx 24rpx;
  background: linear-gradient(135deg, #22d1df 0%, #1395d6 100%);
  color: #fff;
}

.eyebrow {
  display: block;
  font-size: 24rpx;
  opacity: 0.84;
}

.hero-title {
  display: block;
  margin-top: 4rpx;
  font-size: 44rpx;
  font-weight: 800;
}

.hero-actions {
  display: flex;
  gap: 16rpx;
}

.icon-btn {
  width: 68rpx;
  height: 68rpx;
  border-radius: 34rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.42);
  color: #fff;
  font-weight: 700;
}

.icon-btn.primary {
  background: #ff5c9a;
  border-color: #ff5c9a;
  font-size: 36rpx;
}

.summary-strip {
  margin: -2rpx 24rpx 18rpx;
  background: #fff;
  border-radius: 0 0 18rpx 18rpx;
  display: grid;
  grid-template-columns: 1fr 1.5fr 1.5fr;
  box-shadow: 0 10rpx 26rpx rgba(15, 86, 120, 0.08);
}

.summary-item {
  padding: 20rpx 18rpx;
  border-right: 1px solid #edf1f4;
}

.summary-item:last-child {
  border-right: 0;
}

.summary-value {
  display: block;
  color: #113f5c;
  font-size: 32rpx;
  font-weight: 800;
}

.summary-label {
  display: block;
  margin-top: 4rpx;
  color: #8a98a8;
  font-size: 22rpx;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 0 24rpx 18rpx;
}

.form-panel {
  margin: 0 24rpx 20rpx;
  padding: 22rpx;
  border-radius: 12rpx;
  background: #fff;
  box-shadow: 0 10rpx 24rpx rgba(18, 84, 110, 0.08);
}

.form-input {
  height: 78rpx;
  border-radius: 10rpx;
  border: 1px solid #e4ebf0;
  padding: 0 20rpx;
  margin-bottom: 14rpx;
  font-size: 28rpx;
  background: #fff;
}

.form-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14rpx;
}

.plain-btn,
.solid-btn {
  height: 74rpx;
  border-radius: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
}

.plain-btn {
  color: #66737f;
  background: #f1f3f5;
}

.solid-btn {
  color: #fff;
  background: #16b7d7;
}

.search-input {
  flex: 1;
  height: 76rpx;
  border-radius: 12rpx;
  background: #fff;
  padding: 0 24rpx;
  font-size: 28rpx;
  border: 1px solid #e4ebf0;
}

.sort-tabs {
  display: flex;
  background: #e9eef2;
  border-radius: 999rpx;
  padding: 6rpx;
}

.sort-tab {
  min-width: 74rpx;
  text-align: center;
  padding: 10rpx 12rpx;
  border-radius: 999rpx;
  color: #6b7886;
  font-size: 24rpx;
}

.sort-tab.active {
  background: #fff;
  color: #13a7cb;
  font-weight: 700;
}

.ledger-list {
  padding: 0 24rpx;
}

.personal-mode-card {
  margin: 0 24rpx 24rpx;
  min-height: 152rpx;
  padding: 24rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border: 1px solid #dce9ef;
  box-shadow: 0 10rpx 24rpx rgba(18, 84, 110, 0.08);
}

.personal-mode-card.active {
  border-color: #13a7cb;
  background: linear-gradient(135deg, #f1fbff 0%, #fff 100%);
}

.personal-mode-sub {
  display: block;
  margin-top: 8rpx;
  color: #7d8996;
  font-size: 24rpx;
}

.ledger-card {
  position: relative;
  overflow: hidden;
  min-height: 266rpx;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  color: #113f5c;
  background: linear-gradient(160deg, #ecfbff 0%, #fffdfd 48%, #ffe4e2 100%);
  box-shadow: 0 12rpx 28rpx rgba(18, 84, 110, 0.13);
  border: 1px solid rgba(19, 167, 203, 0.18);
}

.ledger-card.current {
  border-color: #13a7cb;
}

.card-bg {
  position: absolute;
  inset: 0;
  opacity: 0.34;
  background: linear-gradient(180deg, rgba(48, 184, 217, 0.2), rgba(255, 115, 130, 0.2));
  pointer-events: none;
}

.ledger-top,
.member-row,
.ledger-footer,
.ledger-metrics {
  position: relative;
  z-index: 1;
}

.ledger-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.share-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(29, 196, 173, 0.18);
  color: #0f9f91;
  font-size: 22rpx;
}

.ledger-name {
  display: block;
  margin-top: 12rpx;
  font-size: 38rpx;
  font-weight: 800;
}

.current-tag {
  color: #13a7cb;
  font-size: 24rpx;
  font-weight: 700;
}

.member-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 28rpx;
}

.avatars {
  display: flex;
  align-items: center;
}

.avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 28rpx;
  margin-right: -10rpx;
  border: 3rpx solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24rpx;
  font-weight: 700;
  background: #18b7d8;
}

.avatar:nth-child(2) {
  background: #ff7b8c;
}

.avatar:nth-child(3) {
  background: #2fb68d;
}

.avatar.add {
  background: #ff5c9a;
  font-size: 36rpx;
}

.created {
  color: #6f7e89;
  font-size: 24rpx;
}

.ledger-footer {
  display: flex;
  align-items: flex-end;
  margin-top: 28rpx;
}

.footer-action {
  margin-right: 34rpx;
  color: #1395d6;
  font-size: 30rpx;
  font-weight: 700;
}

.footer-action.danger {
  color: #e04f5f;
}

.balance-block {
  margin-left: auto;
  text-align: right;
}

.balance-label {
  display: block;
  color: #84919c;
  font-size: 24rpx;
}

.balance-value {
  display: block;
  margin-top: 4rpx;
  color: #6c7278;
  font-size: 32rpx;
  font-weight: 800;
}

.ledger-metrics {
  display: flex;
  justify-content: space-between;
  margin-top: 20rpx;
  padding-top: 16rpx;
  border-top: 1px solid rgba(17, 63, 92, 0.08);
  color: #6b7886;
  font-size: 23rpx;
}

.empty-state {
  padding: 80rpx 24rpx;
  text-align: center;
  color: #8a98a8;
}

.empty-title {
  display: block;
  font-size: 34rpx;
  color: #34495e;
  font-weight: 700;
}

.empty-sub {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
}
</style>
