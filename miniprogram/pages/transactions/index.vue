<template>
  <view class="page">
    <view class="card filters">
      <picker mode="selector" :range="periodOptions" @change="onPeriodChange">
        <view class="picker">{{ periodOptions[periodIndex] }}</view>
      </picker>
      <view class="btn-primary mini" @tap="loadTransactions">刷新</view>
    </view>

    <view class="card">
      <view v-if="!transactions.length" class="text-muted">暂无交易数据</view>
      <view v-for="item in transactions" :key="item.id" class="tx-row" @tap="openDetail(item.id)">
        <view class="left">
          <view :class="iconClass(item)">{{ displayCategory(item).slice(0, 1) }}</view>
          <view>
            <text class="cat">{{ displayCategory(item) }}</text>
            <text class="meta">{{ displayMeta(item) }}</text>
          </view>
        </view>
        <text :class="amountClass(item)">
          {{ amountPrefix(item) }}¥{{ formatMoney(item.amount) }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../services/api'
import { formatMoney } from '../../services/utils'

const periodOptions = ['最近', '今天', '本月', '本年']
const periodMap = ['', 'day', 'month', 'year']
const periodIndex = ref(0)
const transactions = ref([])

function onPeriodChange(event) {
  periodIndex.value = Number(event.detail.value || 0)
  loadTransactions()
}

function openDetail(id) {
  uni.navigateTo({ url: `/pages/transaction-detail/index?id=${id}` })
}

function displayCategory(item) {
  if (item.business_type === 'transfer') return '转账'
  if (item.business_type === 'prepay') return '预交款'
  return item.category || '未分类'
}

function displayMeta(item) {
  if (item.business_type === 'transfer') {
    return `${item.account_name || '-'} → ${item.target_account_name || '-'} · ${item.date}`
  }
  const flags = []
  if (item.location_name) flags.push('位置')
  if (item.attachments && item.attachments.length) flags.push('凭证')
  if (item.include_in_stats === false) flags.push('不统计')
  const suffix = flags.length ? ` · ${flags.join(' · ')}` : ''
  return `${item.date || ''} ${item.time || ''}${suffix}`
}

function amountClass(item) {
  if (item.business_type === 'transfer') return 'amt transfer'
  return item.type === 'income' ? 'amt income' : 'amt expense'
}

function amountPrefix(item) {
  if (item.business_type === 'transfer') return ''
  return item.type === 'income' ? '+' : '-'
}

function iconClass(item) {
  if (item.business_type === 'transfer') return 'tx-icon transfer'
  return item.type === 'income' ? 'tx-icon income' : 'tx-icon expense'
}

async function loadTransactions() {
  try {
    const period = periodMap[periodIndex.value]
    const res = await api.get('/api/transactions', { period, limit: 100 })
    transactions.value = res.transactions || []
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

onShow(loadTransactions)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.page {
  padding-top: 12rpx;
}

.filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.picker {
  border: 1px solid $border;
  border-radius: $radius-sm;
  padding: 12rpx 16rpx;
}

.mini {
  padding: 12rpx 20rpx;
  font-size: 24rpx;
}

.tx-row {
  min-height: 104rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid $border;
}

.tx-row:last-child {
  border-bottom: 0;
}

.left {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-width: 0;
}

.tx-icon {
  width: 66rpx;
  height: 66rpx;
  border-radius: 33rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 26rpx;
  font-weight: 800;
}

.tx-icon.expense {
  background: #ff7b8c;
}

.tx-icon.income {
  background: #10b981;
}

.tx-icon.transfer {
  background: #607080;
}

.cat {
  display: block;
  color: $text-primary;
  font-size: 30rpx;
  font-weight: 700;
}

.meta {
  display: block;
  color: $text-secondary;
  font-size: 22rpx;
  margin-top: 4rpx;
  max-width: 420rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.amt {
  font-weight: 800;
  font-size: 32rpx;
}

.amt.income {
  color: #10b981;
}

.amt.expense {
  color: #ef4444;
}

.amt.transfer {
  color: #607080;
}
</style>
