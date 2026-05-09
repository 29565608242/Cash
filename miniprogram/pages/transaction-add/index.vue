<template>
  <view class="page">
    <view class="card">
      <view class="type-switch">
        <view :class="tx.type === 'income' ? 'seg active' : 'seg'" @tap="tx.type = 'income'">收入</view>
        <view :class="tx.type === 'expense' ? 'seg active' : 'seg'" @tap="tx.type = 'expense'">支出</view>
      </view>

      <amount-input v-model="tx.amount" placeholder="金额" />
      <view style="height: 14rpx"></view>

      <picker mode="selector" :range="categories" @change="onCategoryChange">
        <view class="picker">分类：{{ tx.category || '请选择' }}</view>
      </picker>

      <picker mode="selector" :range="accountOptions" :value="accountIndex" @change="onAccountChange">
        <view class="picker">账户：{{ accountText }}</view>
      </picker>

      <picker mode="selector" :range="currencyOptions" :value="currencyIndex" @change="onCurrencyChange">
        <view class="picker">币种：{{ tx.currency }}</view>
      </picker>

      <view v-if="tx.currency !== 'CNY'" class="hint">
        非人民币将按后端实时汇率折算为人民币入账
      </view>

      <input class="input" v-model="tx.date" placeholder="日期 YYYY-MM-DD" />
      <input class="input" v-model="tx.time" placeholder="时间 HH:mm:ss" />
      <input class="input" v-model="tx.remark" placeholder="备注（可选）" />

      <view class="btn-primary" @tap="submit">保存交易</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { nowTime, today } from '../../services/utils'

const tx = reactive({
  type: 'expense',
  amount: '',
  category: '',
  account_id: null,
  currency: 'CNY',
  date: today(),
  time: nowTime(),
  remark: '',
})

const categoriesRaw = ref([])
const categories = ref([])
const accounts = ref([])

const currencyOptions = [
  'CNY',
  'USD',
  'EUR',
  'GBP',
  'JPY',
  'HKD',
  'KRW',
  'SGD',
  'THB',
  'TWD',
  'AUD',
  'CAD',
  'MYR',
]

const accountOptions = computed(() =>
  accounts.value.map((item) => `${item.name} · ¥${Number(item.balance || 0).toFixed(2)}`)
)

const accountIndex = computed(() => {
  const idx = accounts.value.findIndex((item) => item.id === tx.account_id)
  return idx >= 0 ? idx : 0
})

const accountText = computed(() => {
  if (!accounts.value.length) return '暂无可用账户'
  const idx = accountIndex.value
  return accountOptions.value[idx] || '请选择'
})

const currencyIndex = computed(() => {
  const idx = currencyOptions.findIndex((code) => code === tx.currency)
  return idx >= 0 ? idx : 0
})

function syncCategories() {
  categories.value = categoriesRaw.value
    .filter((item) => item.type === tx.type)
    .map((item) => item.name)
  if (!categories.value.includes(tx.category)) {
    tx.category = categories.value[0] || ''
  }
}

watch(
  () => tx.type,
  () => syncCategories()
)

function onCategoryChange(event) {
  const idx = Number(event.detail.value || 0)
  tx.category = categories.value[idx] || ''
}

function onAccountChange(event) {
  const idx = Number(event.detail.value || 0)
  const selected = accounts.value[idx]
  tx.account_id = selected ? selected.id : null
}

function onCurrencyChange(event) {
  const idx = Number(event.detail.value || 0)
  tx.currency = currencyOptions[idx] || 'CNY'
}

async function loadCategories() {
  try {
    const res = await api.get(endpoints.categories)
    categoriesRaw.value = res.categories || []
    syncCategories()
  } catch (error) {
    uni.showToast({ title: error.message || '加载分类失败', icon: 'none' })
  }
}

async function loadAccounts() {
  try {
    const res = await api.get(endpoints.accounts)
    accounts.value = res.accounts || []
    if (!accounts.value.length) {
      tx.account_id = null
      return
    }
    if (!accounts.value.some((item) => item.id === tx.account_id)) {
      tx.account_id = accounts.value[0].id
    }
  } catch (error) {
    uni.showToast({ title: error.message || '加载账户失败', icon: 'none' })
  }
}

async function submit() {
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

  try {
    await api.post(endpoints.transactions, {
      type: tx.type,
      amount,
      category: tx.category,
      date: tx.date || today(),
      time: tx.time || nowTime(),
      remark: tx.remark,
      account_id: tx.account_id,
      currency: tx.currency,
    })

    uni.showToast({ title: '保存成功', icon: 'success' })
    tx.amount = ''
    tx.remark = ''
    tx.currency = 'CNY'
    tx.time = nowTime()
    uni.switchTab({ url: '/pages/index/index' })
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  }
}

onShow(() => {
  loadCategories()
  loadAccounts()
})
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.page {
  padding-top: 12rpx;
}

.type-switch {
  display: flex;
  background: #f3f5f8;
  border-radius: $radius-md;
  padding: 8rpx;
  margin-bottom: 16rpx;
}

.seg {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  border-radius: $radius-sm;
}

.active {
  background: #fff;
  color: $primary;
  font-weight: 700;
}

.input {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 0 22rpx;
  margin-bottom: 14rpx;
}

.picker {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 24rpx 22rpx 0;
  margin-bottom: 14rpx;
}

.hint {
  margin: 2rpx 2rpx 14rpx;
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.4;
  background: #f8fafc;
  border: 1px dashed $border;
  border-radius: $radius-sm;
  padding: 12rpx 16rpx;
}
</style>
