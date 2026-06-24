<template>
  <view class="page-wrap">
    <view class="card" v-if="tx">
      <view class="row">
        <view>{{ displayCategory(tx) }}</view>
        <view :style="{ color: amountColor(tx) }">
          {{ amountPrefix(tx) }}¥{{ formatMoney(tx.amount) }}
        </view>
      </view>

      <view class="text-muted" style="margin-top: 10rpx">{{ tx.date }} {{ tx.time }}</view>
      <view class="text-muted" style="margin-top: 8rpx">账户：{{ tx.account_name || '-' }}</view>
      <view v-if="tx.business_type === 'transfer'" class="text-muted" style="margin-top: 8rpx">
        转入账户：{{ tx.target_account_name || '-' }}
      </view>
      <view v-if="tx.include_in_stats === false" class="badge-line">不参与统计</view>

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

      <view v-if="tx.split_details && tx.split_details.length" class="info-box">
        <view class="info-title">AA 分摊</view>
        <view v-for="item in tx.split_details" :key="item.user_id" class="info-line">
          {{ item.username || item.user_id }}：¥{{ formatMoney(item.amount) }}
        </view>
      </view>

      <view v-if="tx.location_name" class="info-box">
        <view class="info-title">位置</view>
        <view class="info-line">{{ tx.location_name }}</view>
      </view>

      <view v-if="tx.attachments && tx.attachments.length" class="info-box">
        <view class="info-title">凭证</view>
        <view class="image-grid">
          <image
            v-for="item in tx.attachments"
            :key="item.url"
            class="proof"
            :src="assetUrl(item.url)"
            mode="aspectFill"
            @tap="previewImage(item.url)"
          />
        </view>
      </view>

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
import { assetUrl } from '../../config/index'

const tx = ref(null)

function formatRate(value) {
  const num = Number(value || 0)
  return num ? num.toFixed(6) : '-'
}

function displayCategory(item) {
  if (item.business_type === 'transfer') return '转账'
  if (item.business_type === 'prepay') return '预交款'
  return item.category
}

function amountColor(item) {
  if (item.business_type === 'transfer') return '#607080'
  return item.type === 'income' ? '#10b981' : '#ef4444'
}

function amountPrefix(item) {
  if (item.business_type === 'transfer') return ''
  return item.type === 'income' ? '+' : '-'
}

function previewImage(url) {
  uni.previewImage({
    urls: (tx.value.attachments || []).map((item) => assetUrl(item.url)),
    current: assetUrl(url),
  })
}

onLoad(async (options) => {
  const id = options.id
  await loadOne(id)
})

async function loadOne(id) {
  try {
    const res = await api.get(`${endpoints.transactions}/${id}`)
    tx.value = res.transaction || null
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

.badge-line {
  display: inline-flex;
  margin-top: 12rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
  color: #64748b;
  font-size: 24rpx;
}

.info-box {
  margin-top: 18rpx;
  padding: 16rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  background: #fff;
}

.info-title {
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 8rpx;
}

.info-line {
  color: $text-secondary;
  font-size: 26rpx;
  line-height: 1.7;
}

.image-grid {
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.proof {
  width: 150rpx;
  height: 150rpx;
  border-radius: 10rpx;
  background: #f1f5f9;
}
</style>
