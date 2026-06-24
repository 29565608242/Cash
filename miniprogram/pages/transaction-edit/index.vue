<template>
  <view class="edit-page">
    <view class="topbar">
      <text class="back" @tap="goBack">‹</text>
      <text class="title">编辑记账</text>
      <text class="save-link" @tap="submit">保存</text>
    </view>

    <view class="tabs">
      <view
        v-for="item in modeTabs"
        :key="item.value"
        :class="activeMode === item.value ? 'tab active' : 'tab'"
        @tap="setMode(item.value)"
      >
        {{ item.label }}
      </view>
    </view>

    <view class="amount-card">
      <view class="amount-row">
        <picker mode="selector" :range="currencyLabels" :value="currencyIndex" @change="onCurrencyChange">
          <view class="currency-pill">{{ form.currency }}</view>
        </picker>
        <input class="amount-input" type="digit" v-model="form.amount" placeholder="0" />
        <text class="clear" @tap="form.amount = ''">×</text>
        <picker mode="date" :value="form.date" @change="onDateChange">
          <view class="date-pill">{{ form.date || '今天' }}</view>
        </picker>
      </view>
      <view v-if="form.currency !== 'CNY'" class="amount-hint">外币金额会由后端按实时汇率折算为人民币</view>
    </view>

    <view class="category-panel">
      <view class="category-grid">
        <view
          v-for="item in categories"
          :key="item"
          :class="form.category === item ? 'category-item active' : 'category-item'"
          @tap="form.category = item"
        >
          <view class="category-icon">{{ categoryIcon(item) }}</view>
          <text class="category-name">{{ item }}</text>
        </view>
      </view>
    </view>

    <view class="detail-list">
      <picker mode="selector" :range="accountOptions" :value="accountIndex" @change="onAccountChange">
        <view class="detail-row">
          <text class="row-label">{{ sourceAccountLabel }}</text>
          <text class="row-value">{{ accountText }}</text>
          <text class="row-arrow">›</text>
        </view>
      </picker>

      <picker
        v-if="form.business_type === 'transfer'"
        mode="selector"
        :range="targetAccountOptions"
        :value="targetAccountIndex"
        @change="onTargetAccountChange"
      >
        <view class="detail-row">
          <text class="row-label">转入账户</text>
          <text class="row-value">{{ targetAccountText }}</text>
          <text class="row-arrow">›</text>
        </view>
      </picker>

      <view v-if="form.business_type === 'normal' && members.length" class="detail-row compact">
        <text class="row-label">付款人</text>
        <view class="member-chips">
          <view
            v-for="member in members"
            :key="member.user_id"
            :class="form.payer_user_id === member.user_id ? 'member-chip active' : 'member-chip'"
            @tap="form.payer_user_id = member.user_id"
          >
            {{ memberLabel(member) }}
          </view>
        </view>
      </view>

      <view v-if="form.business_type === 'normal' && form.type === 'expense' && members.length" class="detail-row compact">
        <text class="row-label">参与人</text>
        <view class="member-chips">
          <view
            v-for="member in members"
            :key="member.user_id"
            :class="participantIds.includes(member.user_id) ? 'member-chip active' : 'member-chip'"
            @tap="toggleParticipant(member.user_id)"
          >
            {{ memberLabel(member) }}
          </view>
          <text v-if="participantIds.length > 1" class="split-tip">
            共{{ participantIds.length }}人 · 平均 ¥{{ averageAmount }}
          </text>
        </view>
      </view>
    </view>

    <view class="tag-panel" v-if="quickTags.length">
      <view
        v-for="tag in quickTags"
        :key="tag"
        :class="form.remark === tag ? 'quick-tag active' : 'quick-tag'"
        @tap="form.remark = tag"
      >
        {{ tag }}
      </view>
      <view class="quick-tag minus" @tap="form.remark = ''">-</view>
    </view>

    <view class="remark-panel">
      <textarea
        class="remark"
        v-model="form.remark"
        maxlength="150"
        placeholder="描述这笔记账..."
      />
      <text class="counter">{{ form.remark.length }}/150</text>
      <view class="media-row">
        <view class="media-btn" @tap="pickImage">凭证</view>
        <view :class="location.name ? 'media-btn active' : 'media-btn'" @tap="markLocation">
          {{ location.name ? '已定位' : '位置' }}
        </view>
      </view>
      <view v-if="attachments.length" class="attachment-row">
        <view v-for="item in attachments" :key="item.url" class="attachment-chip">
          <text>{{ item.name || '凭证' }}</text>
          <text class="chip-close" @tap="removeAttachment(item.url)">×</text>
        </view>
      </view>
      <view v-if="location.name" class="location-line">{{ location.name }}</view>
    </view>

    <view class="option-list">
      <view v-if="form.business_type === 'normal' && form.type === 'expense'" class="option-line">
        <view>
          <text class="option-title">需要报销</text>
          <text class="option-desc">保存为待报销支出</text>
        </view>
        <switch :checked="needsReimbursement" @change="needsReimbursement = $event.detail.value" />
      </view>
      <view class="option-line">
        <view>
          <text class="option-title">参与统计</text>
          <text class="option-desc">关闭后不进入余额、报表和预算统计</text>
        </view>
        <switch :checked="includeInStats" @change="includeInStats = $event.detail.value" />
      </view>
    </view>

    <view class="bottom-actions">
      <view class="secondary-btn" @tap="goBack">取消</view>
      <view class="primary-btn" @tap="submit">保存修改</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { store } from '../../store/index'
import { formatMoney, showError, today } from '../../services/utils'

const modeTabs = [
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' },
  { label: '转账', value: 'transfer' },
  { label: '预交款', value: 'prepay' },
]

const currencyOptions = [
  { code: 'CNY', label: '人民币 CNY' },
  { code: 'USD', label: '美元 USD' },
  { code: 'EUR', label: '欧元 EUR' },
  { code: 'GBP', label: '英镑 GBP' },
  { code: 'JPY', label: '日元 JPY' },
  { code: 'HKD', label: '港币 HKD' },
  { code: 'KRW', label: '韩元 KRW' },
  { code: 'SGD', label: '新加坡元 SGD' },
  { code: 'THB', label: '泰铢 THB' },
  { code: 'TWD', label: '新台币 TWD' },
  { code: 'AUD', label: '澳元 AUD' },
  { code: 'CAD', label: '加元 CAD' },
  { code: 'MYR', label: '林吉特 MYR' },
]

const tagMap = {
  餐饮: ['早餐', '午餐', '晚餐', '夜宵', '外卖', '饮料'],
  交通: ['出租', '火车/高铁', '飞机', '大巴', '停车费', '油费'],
  日常: ['上午', '中午', '下午', '晚上', '水费', '电费'],
  住宿: ['酒店', '民宿', '押金', '房费'],
  购物: ['日用品', '服饰', '数码', '家居'],
  娱乐: ['电影', '游戏', '演出', '聚会'],
}

const txId = ref('')
const currentLedgerId = ref(null)
const categoriesRaw = ref([])
const categories = ref([])
const accounts = ref([])
const members = ref([])
const participantIds = ref([])
const needsReimbursement = ref(false)
const includeInStats = ref(true)
const attachments = ref([])
const location = reactive({
  name: '',
  latitude: null,
  longitude: null,
})

const form = reactive({
  type: 'expense',
  business_type: 'normal',
  amount: '',
  category: '',
  date: today(),
  remark: '',
  account_id: null,
  target_account_id: null,
  currency: 'CNY',
  payer_user_id: null,
  reimbursement_status: 'none',
})

const activeMode = computed(() => {
  if (form.business_type === 'transfer' || form.business_type === 'prepay') return form.business_type
  return form.type
})

const currencyLabels = computed(() => currencyOptions.map((item) => item.label))
const currencyIndex = computed(() => {
  const idx = currencyOptions.findIndex((item) => item.code === form.currency)
  return idx >= 0 ? idx : 0
})

const accountOptions = computed(() =>
  accounts.value.map((item) => `${item.name} · ¥${formatMoney(item.balance)}`)
)
const accountIndex = computed(() => {
  const idx = accounts.value.findIndex((item) => item.id === form.account_id)
  return idx >= 0 ? idx : 0
})
const accountText = computed(() => {
  if (!accounts.value.length) return '暂无可用账户'
  return accountOptions.value[accountIndex.value] || '请选择'
})

const targetAccounts = computed(() => accounts.value.filter((item) => item.id !== form.account_id))
const targetAccountOptions = computed(() =>
  targetAccounts.value.map((item) => `${item.name} · ¥${formatMoney(item.balance)}`)
)
const targetAccountIndex = computed(() => {
  const idx = targetAccounts.value.findIndex((item) => item.id === form.target_account_id)
  return idx >= 0 ? idx : 0
})
const targetAccountText = computed(() => {
  if (!targetAccounts.value.length) return '暂无可用账户'
  return targetAccountOptions.value[targetAccountIndex.value] || '请选择'
})

const sourceAccountLabel = computed(() => {
  if (form.business_type === 'transfer') return '转出账户'
  if (form.business_type === 'prepay') return '预交账户'
  return form.type === 'income' ? '收入账户' : '支出账户'
})

const averageAmount = computed(() => {
  const amount = Number(form.amount || 0)
  if (!participantIds.value.length || amount <= 0) return '0.00'
  return formatMoney(amount / participantIds.value.length)
})

const quickTags = computed(() => tagMap[form.category] || [])

watch(
  () => form.type,
  () => syncCategories(true)
)
watch(
  () => form.business_type,
  () => syncCategories(true)
)
watch(
  () => form.account_id,
  () => ensureTargetAccount()
)

onLoad(async (options = {}) => {
  txId.value = options.id || ''
  if (!txId.value) {
    uni.showToast({ title: '缺少交易 ID', icon: 'none' })
    return
  }
  await loadPage()
})

function setMode(mode) {
  if (mode === 'income' || mode === 'expense') {
    form.business_type = 'normal'
    form.type = mode
    includeInStats.value = true
    if (mode === 'income') needsReimbursement.value = false
    return
  }
  form.business_type = mode
  form.type = 'expense'
  form.category = mode === 'transfer' ? '转账' : '预交款'
  includeInStats.value = false
  needsReimbursement.value = false
  ensureTargetAccount()
}

function syncCategories(keepCurrent = false) {
  if (form.business_type === 'transfer') {
    categories.value = ['转账']
    form.category = '转账'
    return
  }
  if (form.business_type === 'prepay') {
    categories.value = ['预交款']
    form.category = '预交款'
    return
  }
  categories.value = categoriesRaw.value
    .filter((item) => item.type === form.type)
    .map((item) => item.name)
  if (!categories.value.includes(form.category)) {
    form.category = keepCurrent && form.category ? form.category : categories.value[0] || ''
  }
}

function categoryIcon(category) {
  return (category || '记').slice(0, 1)
}

function memberLabel(member) {
  return (member.nickname || member.username || '我').slice(0, 1).toUpperCase()
}

function onCurrencyChange(event) {
  const idx = Number(event.detail.value || 0)
  form.currency = currencyOptions[idx] ? currencyOptions[idx].code : 'CNY'
}

function onDateChange(event) {
  form.date = event.detail.value || today()
}

function onAccountChange(event) {
  const idx = Number(event.detail.value || 0)
  const selected = accounts.value[idx]
  form.account_id = selected ? selected.id : null
}

function onTargetAccountChange(event) {
  const idx = Number(event.detail.value || 0)
  const selected = targetAccounts.value[idx]
  form.target_account_id = selected ? selected.id : null
}

function ensureTargetAccount() {
  if (form.business_type !== 'transfer') {
    form.target_account_id = null
    return
  }
  if (!targetAccounts.value.length) {
    form.target_account_id = null
    return
  }
  if (!targetAccounts.value.some((item) => item.id === form.target_account_id)) {
    form.target_account_id = targetAccounts.value[0].id
  }
}

function toggleParticipant(userId) {
  if (participantIds.value.includes(userId)) {
    if (participantIds.value.length <= 1) {
      uni.showToast({ title: '至少保留一位参与人', icon: 'none' })
      return
    }
    participantIds.value = participantIds.value.filter((id) => id !== userId)
    return
  }
  participantIds.value = [...participantIds.value, userId]
}

function normalizeMembers(payload) {
  const list = []
  const seen = new Set()
  const pushMember = (member) => {
    if (!member || !member.user_id || seen.has(member.user_id)) return
    seen.add(member.user_id)
    list.push({
      user_id: member.user_id,
      username: member.username || '',
      nickname: member.nickname || '',
      role: member.role || '',
    })
  }

  pushMember(payload.owner)
  ;(payload.members || []).forEach(pushMember)
  if (!list.length && store.state.user) {
    pushMember({
      user_id: store.state.user.id,
      username: store.state.user.username,
      nickname: store.state.user.nickname,
    })
  }
  return list
}

function resetMembers(list) {
  members.value = list
  if (!members.value.length) return
  if (!members.value.some((item) => item.user_id === form.payer_user_id)) {
    const currentUserId = store.state.user && store.state.user.id
    const mine = members.value.find((item) => item.user_id === currentUserId)
    form.payer_user_id = (mine || members.value[0]).user_id
  }
  if (!participantIds.value.length) {
    participantIds.value = members.value.map((item) => item.user_id)
  }
}

function hydrateTransaction(tx) {
  form.type = tx.type || 'expense'
  form.business_type = tx.business_type || 'normal'
  form.category = tx.category || ''
  form.date = tx.date || today()
  form.remark = tx.remark || ''
  form.account_id = tx.account_id || null
  form.target_account_id = tx.target_account_id || null
  form.currency = tx.currency || 'CNY'
  form.payer_user_id = tx.payer_user_id || null
  form.reimbursement_status = tx.reimbursement_status || 'none'
  form.amount = form.currency !== 'CNY' && tx.original_amount ? `${tx.original_amount}` : `${tx.amount || ''}`
  includeInStats.value = tx.include_in_stats !== false
  needsReimbursement.value = form.reimbursement_status !== 'none'
  attachments.value = Array.isArray(tx.attachments) ? tx.attachments : []
  location.name = tx.location_name || ''
  location.latitude = tx.latitude || null
  location.longitude = tx.longitude || null
  participantIds.value = Array.isArray(tx.split_details)
    ? tx.split_details.map((item) => item.user_id).filter(Boolean)
    : []
}

async function loadTransaction() {
  const res = await api.get(`${endpoints.transactions}/${txId.value}`)
  if (!res.transaction) throw new Error('未找到交易记录')
  hydrateTransaction(res.transaction)
}

async function loadDashboard() {
  const res = await api.get(endpoints.miniapp.dashboard)
  currentLedgerId.value = res.data && res.data.current_ledger_id
}

async function loadCategories() {
  const res = await api.get(endpoints.categories)
  categoriesRaw.value = res.categories || []
  syncCategories(true)
}

async function loadAccounts() {
  const res = await api.get(endpoints.accounts)
  accounts.value = res.accounts || []
  if (!accounts.value.length) {
    form.account_id = null
    return
  }
  if (!accounts.value.some((item) => item.id === form.account_id)) {
    form.account_id = accounts.value[0].id
  }
  ensureTargetAccount()
}

async function loadMembers() {
  if (!currentLedgerId.value) {
    resetMembers([])
    return
  }
  const res = await api.get(`${endpoints.ledgers}/${currentLedgerId.value}/members`)
  resetMembers(normalizeMembers(res))
}

async function loadPage() {
  try {
    await loadTransaction()
    await Promise.all([loadDashboard(), loadCategories(), loadAccounts()])
    await loadMembers()
  } catch (error) {
    showError(error, '加载交易失败')
  }
}

function pickImage() {
  if (attachments.value.length >= 3) {
    uni.showToast({ title: '最多上传 3 张凭证', icon: 'none' })
    return
  }
  uni.chooseImage({
    count: Math.max(1, 3 - attachments.value.length),
    success: async (res) => {
      const paths = res.tempFilePaths || []
      for (const path of paths) {
        try {
          uni.showLoading({ title: '上传中...' })
          const data = await api.upload({
            url: endpoints.miniapp.upload,
            filePath: path,
            formData: { kind: 'transaction' },
          })
          if (data.file && data.file.url) {
            attachments.value.push({
              url: data.file.url,
              name: data.file.name || '凭证',
              type: 'image',
            })
          }
        } catch (error) {
          showError(error, '上传失败')
        } finally {
          uni.hideLoading()
        }
      }
    },
  })
}

function markLocation() {
  if (uni.chooseLocation) {
    uni.chooseLocation({
      success: (res) => {
        location.name = res.name || res.address || '已记录位置'
        location.latitude = res.latitude
        location.longitude = res.longitude
      },
      fail: () => fallbackLocation(),
    })
    return
  }
  fallbackLocation()
}

function fallbackLocation() {
  uni.getLocation({
    type: 'gcj02',
    success: (res) => {
      location.name = '当前位置'
      location.latitude = res.latitude
      location.longitude = res.longitude
    },
    fail: () => uni.showToast({ title: '定位失败', icon: 'none' }),
  })
}

function removeAttachment(url) {
  attachments.value = attachments.value.filter((item) => item.url !== url)
}

function buildSplitDetails(amount) {
  if (form.business_type !== 'normal' || form.type !== 'expense' || participantIds.value.length <= 1) return []
  const selected = members.value.filter((item) => participantIds.value.includes(item.user_id))
  if (selected.length <= 1) return []
  const average = Number((amount / selected.length).toFixed(2))
  return selected.map((member, index) => ({
    user_id: member.user_id,
    username: member.username,
    amount: index === selected.length - 1
      ? Number((amount - average * (selected.length - 1)).toFixed(2))
      : average,
  }))
}

function reimbursementStatus() {
  if (form.business_type !== 'normal' || form.type !== 'expense') return 'none'
  if (!needsReimbursement.value) return 'none'
  return form.reimbursement_status && form.reimbursement_status !== 'none'
    ? form.reimbursement_status
    : 'pending'
}

async function submit() {
  const amount = Number(form.amount)
  if (!amount || amount <= 0) {
    uni.showToast({ title: '请输入正确金额', icon: 'none' })
    return
  }
  if (!form.category) {
    uni.showToast({ title: '请选择分类', icon: 'none' })
    return
  }
  if (!form.account_id) {
    uni.showToast({ title: '请选择账户', icon: 'none' })
    return
  }
  if (form.business_type === 'transfer' && !form.target_account_id) {
    uni.showToast({ title: '请选择转入账户', icon: 'none' })
    return
  }

  try {
    await api.put(`${endpoints.transactions}/${txId.value}`, {
      type: form.type,
      business_type: form.business_type,
      amount,
      category: form.category,
      date: form.date || today(),
      remark: form.remark,
      account_id: form.account_id,
      target_account_id: form.target_account_id,
      currency: form.currency,
      reimbursement_status: reimbursementStatus(),
      payer_user_id: form.business_type === 'normal' ? form.payer_user_id : null,
      split_details: buildSplitDetails(amount),
      include_in_stats: includeInStats.value,
      attachments: attachments.value,
      location_name: location.name,
      latitude: location.latitude,
      longitude: location.longitude,
    })
    uni.showToast({ title: '更新成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 250)
  } catch (error) {
    showError(error, '更新失败')
  }
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.edit-page {
  min-height: 100vh;
  background: #fff;
  padding-bottom: 132rpx;
}

.topbar {
  height: 170rpx;
  padding: 58rpx 34rpx 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, #f3fdff 0%, #ddf6fb 100%);
}

.back,
.save-link {
  width: 96rpx;
}

.back {
  color: #111827;
  font-size: 70rpx;
  line-height: 1;
}

.title {
  flex: 1;
  text-align: center;
  font-size: 42rpx;
  line-height: 1.1;
  font-weight: 800;
  color: #111827;
}

.save-link {
  text-align: right;
  color: #20acd1;
  font-size: 32rpx;
}

.tabs {
  height: 96rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  align-items: center;
  background: #ddf6fb;
}

.tab {
  position: relative;
  text-align: center;
  color: #8a98a8;
  font-size: 32rpx;
  font-weight: 700;
}

.tab.active {
  color: #19acd0;
}

.tab.active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -20rpx;
  width: 52rpx;
  height: 6rpx;
  border-radius: 999rpx;
  transform: translateX(-50%);
  background: #19acd0;
}

.amount-card {
  margin: 12rpx 24rpx 26rpx;
  padding: 26rpx 24rpx;
  border-radius: 14rpx;
  background: #fff;
  box-shadow: 0 12rpx 28rpx rgba(15, 70, 95, 0.12);
}

.amount-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.currency-pill {
  min-width: 92rpx;
  height: 48rpx;
  padding: 0 10rpx;
  border-radius: 6rpx;
  background: #b8bcc1;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
}

.amount-input {
  flex: 1;
  height: 76rpx;
  font-size: 64rpx;
  line-height: 76rpx;
  color: #073a5b;
  font-weight: 800;
}

.clear {
  width: 56rpx;
  height: 56rpx;
  border-radius: 28rpx;
  background: #d1d5db;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
  line-height: 1;
}

.date-pill {
  min-width: 126rpx;
  height: 58rpx;
  border-radius: 10rpx;
  background: #22acd4;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
}

.amount-hint {
  margin-top: 16rpx;
  color: #8a98a8;
  font-size: 24rpx;
}

.category-panel {
  padding: 8rpx 22rpx 26rpx;
  border-bottom: 1px solid #edf1f4;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  row-gap: 30rpx;
}

.category-item {
  display: flex;
  align-items: center;
  flex-direction: column;
  color: #111827;
}

.category-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 36rpx;
  background: #e2e5e8;
  color: #9aa3ad;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
  border: 8rpx solid transparent;
}

.category-item.active .category-icon {
  background: #1fb7d8;
  border-color: #c8f4fa;
  color: #fff;
}

.category-name {
  margin-top: 12rpx;
  font-size: 28rpx;
}

.detail-list {
  border-bottom: 1px solid #edf1f4;
}

.detail-row {
  min-height: 104rpx;
  display: flex;
  align-items: center;
  padding: 0 30rpx;
  border-bottom: 1px solid #edf1f4;
}

.detail-row:last-child {
  border-bottom: 0;
}

.detail-row.compact {
  align-items: flex-start;
  padding-top: 22rpx;
  padding-bottom: 22rpx;
}

.row-label {
  width: 160rpx;
  color: #0f3c5c;
  font-size: 32rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.row-value {
  flex: 1;
  color: #8a98a8;
  text-align: right;
  font-size: 30rpx;
}

.row-arrow {
  margin-left: 18rpx;
  color: #c6cdd4;
  font-size: 46rpx;
}

.member-chips {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.member-chip {
  width: 58rpx;
  height: 58rpx;
  border-radius: 29rpx;
  background: #e7eaee;
  color: #7f8b96;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 800;
}

.member-chip.active {
  background: #22b7d7;
  color: #fff;
}

.split-tip {
  height: 58rpx;
  display: flex;
  align-items: center;
  color: #8a98a8;
  font-size: 26rpx;
}

.tag-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx 18rpx;
  padding: 28rpx 30rpx 12rpx;
}

.quick-tag {
  min-width: 96rpx;
  height: 52rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f3f5;
  color: #7f8b96;
  font-size: 28rpx;
}

.quick-tag.active {
  color: #1395d6;
  background: #e2f7fb;
}

.quick-tag.minus {
  min-width: 110rpx;
  color: #6f7780;
  font-weight: 800;
  font-size: 36rpx;
}

.remark-panel {
  position: relative;
  padding: 16rpx 30rpx 20rpx;
}

.remark {
  width: 100%;
  min-height: 110rpx;
  box-sizing: border-box;
  color: #111827;
  font-size: 30rpx;
}

.counter {
  position: absolute;
  top: 20rpx;
  right: 34rpx;
  color: #c1c7ce;
  font-size: 24rpx;
}

.media-row {
  display: flex;
  gap: 20rpx;
  margin-top: 18rpx;
}

.media-btn {
  width: 112rpx;
  height: 112rpx;
  border: 1px solid #edf1f4;
  color: #9aa7b2;
  background: #fafafa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}

.media-btn.active {
  color: #1199bd;
  border-color: #b9edf5;
  background: #e8fbfd;
}

.attachment-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 18rpx;
}

.attachment-chip {
  max-width: 220rpx;
  height: 48rpx;
  padding: 0 12rpx 0 18rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  color: #1395d6;
  background: #e8fbfd;
  font-size: 24rpx;
}

.chip-close {
  color: #9aa7b2;
  font-size: 32rpx;
  line-height: 1;
}

.location-line {
  margin-top: 14rpx;
  color: #6f7e89;
  font-size: 24rpx;
}

.option-list {
  border-top: 1px solid #edf1f4;
}

.option-line {
  min-height: 104rpx;
  padding: 0 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #edf1f4;
}

.option-title,
.option-desc {
  display: block;
}

.option-title {
  color: #0f3c5c;
  font-size: 30rpx;
  font-weight: 700;
}

.option-desc {
  margin-top: 6rpx;
  color: #8a98a8;
  font-size: 24rpx;
}

.bottom-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 112rpx;
  border-top: 1px solid #19acd0;
  background: #fff;
  z-index: 10;
}

.secondary-btn,
.primary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  font-weight: 700;
}

.secondary-btn {
  color: #19acd0;
  background: #fff;
}

.primary-btn {
  color: #fff;
  background: linear-gradient(135deg, #12afe1 0%, #2bd4dc 100%);
}
</style>
