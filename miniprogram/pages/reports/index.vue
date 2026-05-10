<template>
  <view class="page-wrap report-page">
    <view class="card summary-card">
      <view class="section-title-row">
        <text class="section-title">流水报表</text>
        <text class="btn-switch-ledger" @tap="switchLedger">{{ currentLedgerName }} ▾</text>
      </view>
      <view class="toolbar">
        <picker mode="selector" :range="periodOptions" :value="periodIndex" @change="onPeriodChange">
          <view class="picker">{{ periodOptions[periodIndex] }}</view>
        </picker>
        <view class="btn-primary mini-btn" @tap="reloadAll">刷新</view>
      </view>
      <view class="summary-grid">
        <view class="summary-item">
          <text class="label">收入</text>
          <text class="value income">+￥{{ formatMoney(summary.income) }}</text>
        </view>
        <view class="summary-item">
          <text class="label">支出</text>
          <text class="value expense">-￥{{ formatMoney(summary.expense) }}</text>
        </view>
        <view class="summary-item">
          <text class="label">净额</text>
          <text class="value">￥{{ formatMoney(summary.net) }}</text>
        </view>
        <view class="summary-item">
          <text class="label">笔数</text>
          <text class="value">{{ summary.count || 0 }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <view class="section-subtitle">分类分布（Top 6）</view>
      <view v-if="!topCategories.length" class="text-muted">暂无分类数据</view>
      <view v-for="item in topCategories" :key="`${item.type}-${item.category}`" class="list-item row">
        <view class="cat-left">
          <text class="cat-name">{{ item.category }}</text>
          <text class="cat-type">{{ item.type === 'income' ? '收入' : '支出' }}</text>
        </view>
        <text class="cat-amount">￥{{ formatMoney(item.amount) }}</text>
      </view>
    </view>

    <view class="card">
      <view class="section-subtitle">流水明细（共 {{ transactions.length }} 条）</view>
      <view v-if="!transactions.length" class="text-muted">暂无交易数据</view>
      <view v-for="item in pagedTransactions" :key="item.id" class="tx-row">
        <view class="tx-main" @tap="openDetail(item.id)">
          <text class="tx-cat">{{ item.category }}</text>
          <text class="tx-meta">{{ item.date }} {{ item.time }}</text>
        </view>
        <text :class="item.type === 'income' ? 'tx-amount income' : 'tx-amount expense'">
          {{ item.type === 'income' ? '+' : '-' }}￥{{ formatMoney(item.amount) }}
        </text>
      </view>
      <view v-if="transactions.length > pageSize" class="pagination">
        <view class="page-btn" :class="{ disabled: currentPage <= 1 }" @tap="prevPage">上一页</view>
        <text class="page-info">{{ currentPage }} / {{ totalPages }}</text>
        <view class="page-btn" :class="{ disabled: currentPage >= totalPages }" @tap="nextPage">下一页</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { formatMoney, showError } from '../../services/utils'


const pageSize = 8
const currentPage = ref(1)
const periodOptions = ['最近', '今天', '本月', '本年']
const periodMap = ['', 'day', 'month', 'year']
const reportPeriodMap = ['week', 'week', 'month', 'year']
const periodIndex = ref(0)

const summary = reactive({
  income: 0,
  expense: 0,
  net: 0,
  count: 0,
})
const categoryStats = ref([])
const transactions = ref([])

const totalPages = computed(() => Math.max(1, Math.ceil(transactions.value.length / pageSize)))

const pagedTransactions = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return transactions.value.slice(start, start + pageSize)
})

function prevPage() {
  if (currentPage.value > 1) currentPage.value--
}

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++
}

const topCategories = computed(() => {
  return [...categoryStats.value]
    .sort((a, b) => (b.amount || 0) - (a.amount || 0))
    .slice(0, 6)
})

function openDetail(id) {
  uni.navigateTo({ url: `/pages/transaction-detail/index?id=${id}` })
}

async function loadReport() {
  try {
    const period = reportPeriodMap[periodIndex.value] || 'week'
    const res = await api.get(endpoints.reportAdvanced, { period })
    Object.assign(summary, res.summary || {})
    categoryStats.value = res.category_stats || []
    if (res.current_ledger_name) {
      currentLedgerName.value = res.current_ledger_name
      currentLedgerId.value = res.current_ledger_id
    }
  } catch (error) {
    showError(error, '加载报表失败')
  }
}

async function loadTransactions() {
  try {
    const period = periodMap[periodIndex.value]
    const res = await api.get(endpoints.transactions, { period, limit: 100 })
    transactions.value = res.transactions || []
    currentPage.value = 1
  } catch (error) {
    showError(error, '加载流水失败')
  }
}

function reloadAll() {
  loadReport()
  loadTransactions()
}

function onPeriodChange(event) {
  periodIndex.value = Number(event.detail.value || 0)
  reloadAll()
}

async function switchLedger() {
  try {
    const res = await api.get(endpoints.ledgers)
    const list = res.ledgers || []
    if (!list.length) {
      uni.showToast({ title: '请先创建账本', icon: 'none' })
      setTimeout(() => uni.navigateTo({ url: '/pages/ledgers/index' }), 800)
      return
    }
    const names = list.map((item) => item.name)
    uni.showActionSheet({
      itemList: names,
      success: async (e) => {
        const ledger = list[e.tapIndex]
        await api.post(endpoints.ledgers + '/' + ledger.id + '/switch', {})
        currentLedgerName.value = ledger.name
        currentLedgerId.value = ledger.id
        uni.showToast({ title: '已切换到: ' + ledger.name, icon: 'success' })
        reloadAll()
      }
    })
  } catch (error) {
    uni.showToast({ title: error.message || '失败', icon: 'none' })
  }
}

onShow(reloadAll)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.report-page {
  padding-bottom: 24rpx;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 40rpx;
  font-weight: 700;
  color: #1f2937;
}

.btn-switch-ledger {
  font-size: 24rpx;
  color: $primary;
  padding: 6rpx 16rpx;
  border: 1px solid $primary;
  border-radius: 12rpx;
}

.section-subtitle {
  font-size: 34rpx;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 12rpx;
}

.toolbar {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.picker {
  border: 1px solid $border;
  border-radius: 12rpx;
  padding: 12rpx 18rpx;
  font-size: 26rpx;
  color: #334155;
  background: #fff;
}

.mini-btn {
  padding: 12rpx 24rpx;
  border-radius: 12rpx;
  font-size: 24rpx;
}

.summary-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.summary-item {
  border-radius: 14rpx;
  border: 1px solid $border;
  padding: 16rpx;
  background: #fff;
}

.label {
  font-size: 24rpx;
  color: #6b7280;
}

.value {
  display: block;
  margin-top: 8rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: #1f2937;
}

.value.income {
  color: #0ea371;
}

.value.expense {
  color: #df4b4b;
}

.cat-left {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.cat-name {
  font-size: 28rpx;
  color: #1f2937;
}

.cat-type {
  font-size: 22rpx;
  color: #6b7280;
  background: #f1f5f9;
  border-radius: 999rpx;
  padding: 4rpx 12rpx;
}

.cat-amount {
  font-size: 28rpx;
  font-weight: 700;
}

.tx-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1px solid $border;
}

.tx-row:last-child {
  border-bottom: none;
}

.tx-main {
  display: flex;
  flex-direction: column;
}

.tx-cat {
  font-size: 30rpx;
  color: #1f2937;
}

.tx-meta {
  margin-top: 4rpx;
  color: $text-secondary;
  font-size: 24rpx;
}

.tx-amount {
  min-width: 190rpx;
  text-align: right;
  font-size: 34rpx;
  font-weight: 700;
}

.tx-amount.income {
  color: #0ea371;
}

.tx-amount.expense {
  color: #df4b4b;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20rpx;
  margin-top: 20rpx;
  padding-top: 16rpx;
  border-top: 1px solid $border;
}

.page-btn {
  padding: 12rpx 28rpx;
  border: 1px solid $primary;
  border-radius: 12rpx;
  font-size: 26rpx;
  color: $primary;
}

.page-btn.disabled {
  opacity: 0.4;
}

.page-info {
  font-size: 26rpx;
  color: $text-secondary;
}
</style>
