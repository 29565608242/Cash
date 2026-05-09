<template>
  <view class="page-wrap index-page">
    <view class="card panel panel-quick">
      <view class="quick-head">
        <text class="quick-title">快速记账</text>
        <text class="quick-tip">一键完成常用操作</text>
      </view>
      <view class="quick-grid">
        <view class="quick-card income" @tap="openAdd('income')">
          <view class="quick-icon">+</view>
          <view class="quick-text">
            <text class="quick-main">记一笔收入</text>
            <text class="quick-sub">快速添加收入记录</text>
          </view>
        </view>
        <view class="quick-card expense" @tap="openAdd('expense')">
          <view class="quick-icon">-</view>
          <view class="quick-text">
            <text class="quick-main">记一笔支出</text>
            <text class="quick-sub">快速添加支出记录</text>
          </view>
        </view>
        <view class="quick-card smart" @tap="go('/pages/smart-bookkeeping/index')">
          <view class="quick-icon">AI</view>
          <view class="quick-text">
            <text class="quick-main">智能记账</text>
            <text class="quick-sub">一句话 / 粘贴文本 / 识别结果</text>
          </view>
        </view>
      </view>
    </view>

    <view class="card panel">
      <view class="section-title">数据概览</view>
      <view class="stats-grid">
        <view class="kpi kpi-income">
          <view class="kpi-title">今日收入</view>
          <view class="kpi-value">￥{{ formatMoney(state.summary.today_income) }}</view>
        </view>
        <view class="kpi kpi-expense">
          <view class="kpi-title">今日支出</view>
          <view class="kpi-value">￥{{ formatMoney(state.summary.today_expense) }}</view>
        </view>
        <view class="kpi kpi-balance">
          <view class="kpi-title">月净额</view>
          <view class="kpi-value">￥{{ formatMoney(state.summary.month_balance) }}</view>
        </view>
        <view class="kpi kpi-total">
          <view class="kpi-title">总资产</view>
          <view class="kpi-value">￥{{ formatMoney(state.summary.balance) }}</view>
        </view>
      </view>
    </view>

    <view class="card panel">
      <view class="section-title">功能入口</view>
      <view class="entry-grid">
        <view class="entry-item" @tap="go('/pages/ledgers/index')">账本管理</view>
        <view class="entry-item" @tap="go('/pages/budget/index')">预算管理</view>
        <view class="entry-item" @tap="go('/pages/loans/index')">借贷管理</view>
        <view class="entry-item" @tap="go('/pages/reimbursement/index')">报销管理</view>
        <view class="entry-item" @tap="go('/pages/recurring/index')">周期账单</view>
        <view class="entry-item" @tap="go('/pages/reports/index')">流水报表</view>
        <view class="entry-item" @tap="go('/pages/ai-analysis/index')">AI 分析</view>
      </view>
    </view>

    <view class="card panel">
      <view class="section-title">最近交易</view>
      <view v-if="!state.recent_transactions.length" class="empty text-muted">暂无交易记录</view>
      <view v-for="item in state.recent_transactions" :key="item.id" class="tx-row">
        <view>
          <text class="tx-cat">{{ item.category }}</text>
          <text class="tx-time">{{ item.date }} {{ item.time }}</text>
        </view>
        <text :class="item.type === 'income' ? 'tx-amount income' : 'tx-amount expense'">
          {{ item.type === 'income' ? '+' : '-' }}￥{{ formatMoney(item.amount) }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '../../services/api'
import { formatMoney } from '../../services/utils'

const state = reactive({
  summary: {
    today_income: 0,
    today_expense: 0,
    month_balance: 0,
    balance: 0,
  },
  recent_transactions: [],
})

async function loadDashboard() {
  try {
    const res = await api.get('/api/miniapp/dashboard')
    const payload = res.data || {}
    state.summary = payload.summary || state.summary
    state.recent_transactions = payload.recent_transactions || []
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

function openAdd(type) {
  uni.navigateTo({ url: `/pages/transaction-add/index?type=${type}` })
}

function go(url) {
  if (url === '/pages/reports/index') {
    uni.switchTab({ url })
    return
  }
  uni.navigateTo({ url })
}

onShow(loadDashboard)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.index-page {
  padding-bottom: 30rpx;
}

.panel {
  background: rgba(255, 255, 255, 0.92);
}

.section-title {
  font-size: 40rpx;
  font-weight: 700;
  margin-bottom: 16rpx;
  color: #1f2937;
}

.panel-quick {
  background: linear-gradient(180deg, #ffffff 0%, #f8faff 100%);
  border: 1px solid #dbe6ff;
}

.quick-head {
  margin-bottom: 16rpx;
}

.quick-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #1f2937;
}

.quick-tip {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.quick-card {
  border-radius: 18rpx;
  padding: 20rpx;
  border: 1px solid $border;
  background: #fff;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.quick-card.smart {
  grid-column: span 2;
}

.quick-card.income {
  border-color: #caefdf;
}

.quick-card.expense {
  border-color: #ffd5d5;
}

.quick-card.smart {
  border-color: #d7ddff;
  background: #f5f7ff;
}

.quick-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.quick-card.income .quick-icon {
  background: #13b884;
}

.quick-card.expense .quick-icon {
  background: #ef4b4b;
}

.quick-card.smart .quick-icon {
  background: linear-gradient(135deg, #6078df 0%, #6d49b7 100%);
  font-size: 28rpx;
}

.quick-main {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #1f2937;
}

.quick-sub {
  display: block;
  margin-top: 4rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.kpi {
  border-radius: 18rpx;
  padding: 20rpx;
  border: 1px solid $border;
  background: #fff;
}

.kpi-income {
  border-left: 8rpx solid #20b486;
}

.kpi-expense {
  border-left: 8rpx solid #ef5353;
}

.kpi-balance {
  border-left: 8rpx solid #5b78e8;
}

.kpi-total {
  border-left: 8rpx solid #6f53bf;
}

.kpi-title {
  color: #6b7280;
  font-size: 24rpx;
}

.kpi-value {
  margin-top: 10rpx;
  font-size: 44rpx;
  font-weight: 700;
  color: #1f2937;
}

.entry-grid {
  margin-top: 8rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.entry-item {
  text-align: center;
  padding: 22rpx 10rpx;
  border-radius: 14rpx;
  background: #eef2fb;
  font-size: 28rpx;
  color: #334155;
  border: 1px solid #d9e2f5;
}

.empty {
  margin-top: 16rpx;
}

.tx-row {
  margin-top: 10rpx;
  padding: 14rpx 0;
  border-bottom: 1px solid $border;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tx-row:last-child {
  border-bottom: none;
}

.tx-cat {
  display: block;
  font-size: 34rpx;
}

.tx-time {
  display: block;
  margin-top: 4rpx;
  color: $text-secondary;
  font-size: 26rpx;
}

.tx-amount {
  min-width: 180rpx;
  text-align: right;
  font-size: 44rpx;
  font-weight: 700;
}

.tx-row .income {
  color: #0ea371;
}

.tx-row .expense {
  color: #df4b4b;
}
</style>
