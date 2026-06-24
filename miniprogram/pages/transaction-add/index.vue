<template>
  <view class="record-page">
    <view class="topbar">
      <text class="back" @tap="goBack">‹</text>
      <view class="title-wrap" @tap="switchLedger">
        <text class="title">{{ currentLedgerName }}</text>
        <text class="sync">↻</text>
      </view>
      <text class="save-link" @tap="submit(false)">保存</text>
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
          <view class="currency-pill">{{ tx.currency }}</view>
        </picker>
        <input class="amount-input" type="digit" v-model="tx.amount" placeholder="0" />
        <text class="clear" @tap="clearAmount">×</text>
        <picker mode="date" :value="tx.date" @change="onDateChange">
          <view class="date-pill">{{ dateLabel }}</view>
        </picker>
      </view>
      <view v-if="tx.currency !== 'CNY'" class="amount-hint">外币会按后端汇率折算成人民币入账</view>
    </view>

    <view class="category-panel">
      <view class="category-grid">
        <view
          v-for="item in categories"
          :key="item"
          :class="tx.category === item ? 'category-item active' : 'category-item'"
          @tap="selectCategory(item)"
        >
          <view class="category-icon">{{ categoryIcon(item) }}</view>
          <text class="category-name">{{ item }}</text>
        </view>
      </view>
      <view class="pager-dot">
        <text class="dot active"></text>
        <text class="dot"></text>
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
        v-if="tx.business_type === 'transfer'"
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

      <view v-if="tx.business_type === 'normal' && members.length" class="detail-row compact">
        <text class="row-label">付款人</text>
        <view class="member-chips">
          <view
            v-for="member in members"
            :key="member.user_id"
            :class="tx.payer_user_id === member.user_id ? 'member-chip active' : 'member-chip'"
            @tap="tx.payer_user_id = member.user_id"
          >
            {{ memberLabel(member) }}
          </view>
        </view>
      </view>

      <view v-if="tx.business_type === 'normal' && tx.type === 'expense' && members.length" class="detail-row compact">
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
          <text class="split-tip" v-if="participantIds.length > 1">
            共{{ participantIds.length }}人 · 平均 ¥{{ averageAmount }}
          </text>
        </view>
      </view>
    </view>

    <view class="tag-panel" v-if="quickTags.length">
      <view
        v-for="tag in quickTags"
        :key="tag"
        :class="tx.remark === tag ? 'quick-tag active' : 'quick-tag'"
        @tap="tx.remark = tag"
      >
        {{ tag }}
      </view>
      <view class="quick-tag plus" @tap="focusRemark">+</view>
      <view class="quick-tag minus" @tap="tx.remark = ''">-</view>
    </view>

    <view class="remark-panel">
      <textarea
        class="remark"
        v-model="tx.remark"
        maxlength="150"
        placeholder="描述这笔记账..."
      />
      <text class="counter">{{ tx.remark.length }}/150</text>
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

    <view class="option-row">
      <view
        v-if="tx.business_type === 'normal' && tx.type === 'expense'"
        :class="needsReimbursement ? 'option active' : 'option'"
        @tap="needsReimbursement = !needsReimbursement"
      >
        需要报销
      </view>
      <view class="option" @tap="goRecurring">周期账单</view>
      <view :class="includeInStats ? 'option' : 'option active'" @tap="includeInStats = !includeInStats">
        不参与统计
      </view>
    </view>

    <view class="bottom-actions">
      <view class="secondary-btn" @tap="submit(true)">再记一笔</view>
      <view class="primary-btn" @tap="submit(false)">保存</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
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
  交通: ['出租', '火车/高铁', '飞机', '大巴', '船票', '停车费', '过路费', '油费', '汽车保养'],
  日常: ['上午', '中午', '下午', '晚上', '水费', '电费', '煤气费', '电视费'],
  住宿: ['酒店', '民宿', '押金', '房费'],
  购物: ['日用品', '服饰', '数码', '家居'],
  娱乐: ['电影', '游戏', '演出', '聚会'],
  医疗: ['挂号', '药品', '检查'],
}

const iconMap = {
  日常: '日',
  餐饮: '餐',
  交通: '行',
  住宿: '宿',
  门票: '票',
  通讯: '讯',
  购物: '购',
  酒水: '酒',
  娱乐: '乐',
  医疗: '医',
  工资: '薪',
  奖金: '奖',
  投资收益: '投',
  兼职: '兼',
  红包: '红',
  报销收入: '报',
  其他收入: '收',
  其他支出: '支',
  转账: '转',
  预交款: '预',
}

const tx = reactive({
  type: 'expense',
  business_type: 'normal',
  amount: '',
  category: '',
  account_id: null,
  target_account_id: null,
  currency: 'CNY',
  date: today(),
  remark: '',
  payer_user_id: null,
})

const currentLedgerId = ref(null)
const currentLedgerName = ref('当前账本')
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

const activeMode = computed(() => {
  if (tx.business_type === 'transfer' || tx.business_type === 'prepay') return tx.business_type
  return tx.type
})

const currencyLabels = computed(() => currencyOptions.map((item) => item.label))
const currencyIndex = computed(() => {
  const idx = currencyOptions.findIndex((item) => item.code === tx.currency)
  return idx >= 0 ? idx : 0
})

const accountOptions = computed(() =>
  accounts.value.map((item) => `${item.name} · ¥${formatMoney(item.balance)}`)
)
const accountIndex = computed(() => {
  const idx = accounts.value.findIndex((item) => item.id === tx.account_id)
  return idx >= 0 ? idx : 0
})
const accountText = computed(() => {
  if (!accounts.value.length) return '暂无可用账户'
  return accountOptions.value[accountIndex.value] || '请选择'
})

const sourceAccountLabel = computed(() => {
  if (tx.business_type === 'transfer') return '转出账户'
  if (tx.business_type === 'prepay') return '预交账户'
  return tx.type === 'income' ? '收入账户' : '支出账户'
})

const targetAccounts = computed(() => accounts.value.filter((item) => item.id !== tx.account_id))
const targetAccountOptions = computed(() =>
  targetAccounts.value.map((item) => `${item.name} · ¥${formatMoney(item.balance)}`)
)
const targetAccountIndex = computed(() => {
  const idx = targetAccounts.value.findIndex((item) => item.id === tx.target_account_id)
  return idx >= 0 ? idx : 0
})
const targetAccountText = computed(() => {
  if (!targetAccounts.value.length) return '暂无可用账户'
  return targetAccountOptions.value[targetAccountIndex.value] || '请选择'
})

const dateLabel = computed(() => (tx.date === today() ? '今天' : tx.date))
const averageAmount = computed(() => {
  const amount = Number(tx.amount || 0)
  if (!participantIds.value.length || amount <= 0) return '0.00'
  return formatMoney(amount / participantIds.value.length)
})
const quickTags = computed(() => tagMap[tx.category] || [])

watch(
  () => tx.type,
  () => syncCategories()
)
watch(
  () => tx.business_type,
  () => syncCategories()
)
watch(
  () => tx.account_id,
  () => ensureTargetAccount()
)

onLoad((options = {}) => {
  if (options.type === 'income' || options.type === 'expense') {
    setMode(options.type)
  }
})

onShow(() => {
  const pendingType = uni.getStorageSync('cash_add_type')
  if (pendingType === 'income' || pendingType === 'expense') {
    setMode(pendingType)
    uni.removeStorageSync('cash_add_type')
  }
  loadAll()
})

function setMode(type) {
  if (type === 'income' || type === 'expense') {
    tx.business_type = 'normal'
    tx.type = type
    includeInStats.value = true
    needsReimbursement.value = false
    return
  }
  tx.business_type = type
  tx.type = 'expense'
  tx.category = type === 'transfer' ? '转账' : '预交款'
  includeInStats.value = false
  needsReimbursement.value = false
  ensureTargetAccount()
}

function syncCategories() {
  if (tx.business_type === 'transfer') {
    categories.value = ['转账']
    tx.category = '转账'
    return
  }
  if (tx.business_type === 'prepay') {
    categories.value = ['预交款']
    tx.category = '预交款'
    return
  }
  categories.value = categoriesRaw.value
    .filter((item) => item.type === tx.type)
    .map((item) => item.name)
  if (!categories.value.length) {
    categories.value = tx.type === 'income' ? ['工资', '奖金', '红包', '其他收入'] : ['日常', '餐饮', '交通', '住宿', '购物', '娱乐', '医疗']
  }
  if (!categories.value.includes(tx.category)) {
    tx.category = categories.value[0] || ''
  }
}

function selectCategory(category) {
  tx.category = category
}

function categoryIcon(category) {
  return iconMap[category] || (category || '记').slice(0, 1)
}

function memberLabel(member) {
  const name = member.nickname || member.username || '我'
  return name.slice(0, 1).toUpperCase()
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
  if (!members.value.some((item) => item.user_id === tx.payer_user_id)) {
    const currentUserId = store.state.user && store.state.user.id
    const mine = members.value.find((item) => item.user_id === currentUserId)
    tx.payer_user_id = (mine || members.value[0]).user_id
  }
  if (!participantIds.value.length) {
    participantIds.value = members.value.map((item) => item.user_id)
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

function onAccountChange(event) {
  const idx = Number(event.detail.value || 0)
  const selected = accounts.value[idx]
  tx.account_id = selected ? selected.id : null
}

function onTargetAccountChange(event) {
  const idx = Number(event.detail.value || 0)
  const selected = targetAccounts.value[idx]
  tx.target_account_id = selected ? selected.id : null
}

function ensureTargetAccount() {
  if (tx.business_type !== 'transfer') {
    tx.target_account_id = null
    return
  }
  if (!targetAccounts.value.length) {
    tx.target_account_id = null
    return
  }
  if (!targetAccounts.value.some((item) => item.id === tx.target_account_id)) {
    tx.target_account_id = targetAccounts.value[0].id
  }
}

function onCurrencyChange(event) {
  const idx = Number(event.detail.value || 0)
  tx.currency = currencyOptions[idx] ? currencyOptions[idx].code : 'CNY'
}

function onDateChange(event) {
  tx.date = event.detail.value || today()
}

function clearAmount() {
  tx.amount = ''
}

function focusRemark() {
  uni.showToast({ title: '可直接填写备注', icon: 'none' })
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

function goRecurring() {
  uni.navigateTo({ url: '/pages/recurring-add/index' })
}

function goBack() {
  uni.switchTab({ url: '/pages/ledgers/index' })
}

async function loadDashboard() {
  const res = await api.get(endpoints.miniapp.dashboard)
  const payload = res.data || {}
  currentLedgerId.value = payload.current_ledger_id
  currentLedgerName.value = payload.current_ledger_name || currentLedgerName.value
}

async function loadCategories() {
  const res = await api.get(endpoints.categories)
  categoriesRaw.value = res.categories || []
  syncCategories()
}

async function loadAccounts() {
  const res = await api.get(endpoints.accounts)
  accounts.value = res.accounts || []
  if (!accounts.value.length) {
    tx.account_id = null
    return
  }
  if (!accounts.value.some((item) => item.id === tx.account_id)) {
    tx.account_id = accounts.value[0].id
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

async function loadAll() {
  try {
    await loadDashboard()
    await Promise.all([loadCategories(), loadAccounts(), loadMembers()])
  } catch (error) {
    showError(error, '加载记账信息失败')
  }
}

async function switchLedger() {
  try {
    const res = await api.get(endpoints.ledgers)
    const list = res.ledgers || []
    if (!list.length) {
      uni.switchTab({ url: '/pages/ledgers/index' })
      return
    }
    uni.showActionSheet({
      itemList: list.map((item) => item.name),
      success: async (event) => {
        const ledger = list[event.tapIndex]
        await api.post(`${endpoints.ledgers}/${ledger.id}/switch`, {})
        currentLedgerId.value = ledger.id
        currentLedgerName.value = ledger.name
        await loadAll()
        uni.showToast({ title: '已切换账本', icon: 'success' })
      },
    })
  } catch (error) {
    showError(error, '切换失败')
  }
}

function buildSplitDetails(amount) {
  if (tx.business_type !== 'normal' || tx.type !== 'expense' || participantIds.value.length <= 1) return []
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

function resetForm() {
  tx.amount = ''
  tx.remark = ''
  tx.currency = 'CNY'
  needsReimbursement.value = false
  attachments.value = []
  location.name = ''
  location.latitude = null
  location.longitude = null
  includeInStats.value = tx.business_type === 'normal'
}

async function submit(keepAdding) {
  const amount = Number(tx.amount)
  if (!amount || amount <= 0) {
    uni.showToast({ title: '请输入正确金额', icon: 'none' })
    return
  }
  if (!tx.category) {
    uni.showToast({ title: '请选择分类', icon: 'none' })
    return
  }
  if (!tx.account_id) {
    uni.showToast({ title: '请选择账户', icon: 'none' })
    return
  }
  if (tx.business_type === 'transfer' && !tx.target_account_id) {
    uni.showToast({ title: '请选择转入账户', icon: 'none' })
    return
  }

  try {
    await api.post(endpoints.transactions, {
      type: tx.type,
      business_type: tx.business_type,
      amount,
      category: tx.category,
      date: tx.date || today(),
      remark: tx.remark,
      account_id: tx.account_id,
      target_account_id: tx.target_account_id,
      currency: tx.currency,
      reimbursement_status: needsReimbursement.value && tx.business_type === 'normal' ? 'pending' : 'none',
      payer_user_id: tx.business_type === 'normal' ? tx.payer_user_id : null,
      split_details: buildSplitDetails(amount),
      include_in_stats: includeInStats.value,
      attachments: attachments.value,
      location_name: location.name,
      latitude: location.latitude,
      longitude: location.longitude,
    })

    uni.showToast({ title: '保存成功', icon: 'success' })
    resetForm()
    await loadAccounts()
    if (!keepAdding) {
      setTimeout(() => uni.navigateTo({ url: '/pages/transactions/index' }), 350)
    }
  } catch (error) {
    showError(error, '保存失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.record-page {
  min-height: 100vh;
  background: #fff;
  padding-bottom: 132rpx;
}

.topbar {
  height: 184rpx;
  padding: 64rpx 34rpx 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, #f3fdff 0%, #ddf6fb 100%);
}

.back {
  width: 80rpx;
  color: #111827;
  font-size: 70rpx;
  line-height: 1;
}

.title-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  flex: 1;
}

.title {
  font-size: 42rpx;
  line-height: 1.1;
  font-weight: 800;
  color: #111827;
}

.sync {
  font-size: 34rpx;
  color: #111827;
  font-weight: 700;
}

.save-link {
  width: 80rpx;
  text-align: right;
  color: #20acd1;
  font-size: 32rpx;
}

.tabs {
  height: 106rpx;
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
  bottom: -24rpx;
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

.pager-dot {
  display: flex;
  justify-content: center;
  gap: 14rpx;
  margin-top: 26rpx;
}

.dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 7rpx;
  background: #d1d5db;
}

.dot.active {
  width: 36rpx;
  background: #111827;
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

.quick-tag.plus,
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

.option-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
  padding: 24rpx 30rpx 10rpx;
}

.option {
  height: 58rpx;
  border-radius: 999rpx;
  background: #f5f6f7;
  color: #6f7780;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}

.option.active {
  background: #e4f8fb;
  color: #1199bd;
  font-weight: 700;
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
