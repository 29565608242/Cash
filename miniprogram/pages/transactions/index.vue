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
      <view v-for="item in transactions" :key="item.id" class="row">
        <view>
          <text class="cat">{{ item.category }}</text>
          <text class="meta">{{ item.date }} {{ item.time }}</text>
        </view>
        <text :class="item.type === 'income' ? 'amt income' : 'amt expense'">
          {{ item.type === 'income' ? '+' : '-' }}¥{{ formatMoney(item.amount) }}
        </text>
        <view class="btn-line" @tap="openDetail(item.id)">详情</view>
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

async function loadTransactions() {
  try {
    const period = periodMap[periodIndex.value]
    const res = await api.get('/api/transactions', { period, limit: 100 })
    transactions.value = res.transactions || []
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

onShow(() => {
  loadTransactions()
})
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';

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

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16rpx;
}

.cat {
  display: block;
}

.meta {
  display: block;
  color: $text-secondary;
  font-size: 22rpx;
  margin-top: 4rpx;
}

.amt {
  font-weight: 700;
}
</style>
