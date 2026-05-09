<template>
  <view class="page-wrap">
    <view class="card" v-if="tx">
      <view class="row">
        <view>{{ tx.category }}</view>
        <view :style="{ color: tx.type === 'income' ? '#10b981' : '#ef4444' }">
          {{ tx.type === 'income' ? '+' : '-' }}¥{{ formatMoney(tx.amount) }}
        </view>
      </view>

      <view class="text-muted" style="margin-top: 10rpx">{{ tx.date }} {{ tx.time }}</view>
      <view class="text-muted" style="margin-top: 8rpx">账户：{{ tx.account_name || '-' }}</view>

      <view class="money-box" style="margin-top: 12rpx">
        <view v-if="(tx.currency || 'CNY') === 'CNY'" class="money-line">
          人民币金额：¥{{ formatMoney(tx.amount) }}
        </view>
        <view v-else>
          <view class="money-line">原币金额：{{ tx.currency }} {{ formatMoney(tx.original_amount || tx.amount) }}</view>
          <view class="money-line">汇率：1 {{ tx.currency }} = {{ formatRate(tx.exchange_rate) }} CNY</view>
          <view class="money-line">折算人民币：¥{{ formatMoney(tx.amount) }}</view>
        </view>
      </view>

      <view style="margin-top: 14rpx">{{ tx.remark || '无备注' }}</view>

      <view class="actions" style="margin-top: 20rpx">
        <view class="btn-line" @tap="editTx">编辑</view>
        <view class="btn-line" @tap="removeTx">删除</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, formatMoney, showError } from '../../services/utils'

const tx = ref(null)

function formatRate(value) {
  const num = Number(value || 0)
  return num ? num.toFixed(6) : '-'
}

onLoad(async (options) => {
  const id = options.id
  await loadOne(id)
})

async function loadOne(id) {
  try {
    const res = await api.get(endpoints.transactions, { limit: 500 })
    tx.value = (res.transactions || []).find((item) => `${item.id}` === `${id}`) || null
  } catch (error) {
    showError(error, '加载详情失败')
  }
}

function editTx() {
  if (!tx.value) return
  uni.navigateTo({ url: `/pages/transaction-edit/index?id=${tx.value.id}` })
}

async function removeTx() {
  if (!tx.value) return
  const ok = await confirmModal('确认删除该交易？')
  if (!ok) return
  try {
    await api.del(`${endpoints.transactions}/${tx.value.id}`)
    uni.showToast({ title: '删除成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 250)
  } catch (error) {
    showError(error, '删除失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.money-box {
  background: #f8fafc;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 14rpx 16rpx;
}

.money-line {
  color: $text-secondary;
  font-size: 25rpx;
  line-height: 1.6;
}
</style>
