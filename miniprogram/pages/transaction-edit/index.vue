<template>
  <view class="page-wrap">
    <view class="card">
      <picker mode="selector" :range="typeOptions" :value="typeIndex" @change="onTypeChange">
        <view class="input">类型：{{ typeOptions[typeIndex] }}</view>
      </picker>

      <input class="input amount-input" type="digit" v-model="form.amount" placeholder="金额（必填）" />

      <picker mode="selector" :range="categories" @change="onCategoryChange">
        <view class="picker">分类：{{ form.category || '请选择' }}</view>
      </picker>

      <picker mode="selector" :range="accountOptions" :value="accountIndex" @change="onAccountChange">
        <view class="picker">账户：{{ accountText }}</view>
      </picker>

      <picker mode="selector" :range="currencyOptions" :value="currencyIndex" @change="onCurrencyChange">
        <view class="picker">币种：{{ form.currency }}</view>
      </picker>

      <view v-if="form.currency !== 'CNY'" class="hint">
        非人民币将按后端实时汇率折算为人民币入账
      </view>

      <picker mode="date" :value="form.date" @change="onDateChange">
        <view class="picker">日期：{{ form.date }}</view>
      </picker>
      <input class="input" v-model="form.remark" placeholder="备注" />

      <view class="btn-primary" @tap="submit">保存修改</view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { showError } from '../../services/utils'

const txId = ref('')
const txData = ref(null)

const typeOptions = ['支出(expense)', '收入(income)']
const typeIndex = ref(0)

const categoriesRaw = ref([])
const categories = ref([])
const accounts = ref([])

const currencyOptions = [
  '人民币 CNY ¥',
  '美元 USD $',
  '欧元 EUR €',
  '英镑 GBP £',
  '日元 JPY ¥',
  '港币 HKD HK$',
  '韩元 KRW ₩',
  '新加坡元 SGD S$',
  '泰钢 THB ฿',
  '新台币 TWD NT$',
  '澳元 AUD A$',
  '加元 CAD C$',
  '林吉特 MYR RM',
]

const form = reactive({
  type: 'expense',
  amount: '',
  category: '',
  date: '',
  remark: '',
  account_id: null,
  currency: 'CNY',
})

const accountOptions = computed(() =>
  accounts.value.map((item) => `${item.name} · ¥${Number(item.balance || 0).toFixed(2)}`)
)

const accountIndex = computed(() => {
  const idx = accounts.value.findIndex((item) => item.id === form.account_id)
  return idx >= 0 ? idx : 0
})

const accountText = computed(() => {
  if (!accounts.value.length) return '暂无可用账户'
  return accountOptions.value[accountIndex.value] || '请选择'
})

const currencyIndex = computed(() => {
  const idx = currencyCodes.findIndex((code) => code === form.currency)
  return idx >= 0 ? idx : 0
})

function syncCategories() {
  categories.value = categoriesRaw.value
    .filter((item) => item.type === form.type)
    .map((item) => item.name)

  if (!categories.value.includes(form.category)) {
    form.category = categories.value[0] || ''
  }
}

watch(
  () => form.type,
  () => syncCategories()
)

function onTypeChange(e) {
  typeIndex.value = Number(e.detail.value || 0)
  form.type = typeIndex.value === 0 ? 'expense' : 'income'
}

function onCategoryChange(e) {
  const idx = Number(e.detail.value || 0)
  form.category = categories.value[idx] || ''
}

function onAccountChange(e) {
  const idx = Number(e.detail.value || 0)
  const selected = accounts.value[idx]
  form.account_id = selected ? selected.id : null
}

function onCurrencyChange(e) {
  const idx = Number(e.detail.value || 0)
  form.currency = currencyCodes[idx] || 'CNY'
}

function onDateChange(e) {
  form.date = e.detail.value || new Date().toISOString().slice(0, 10)
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
    form.account_id = null
    return
  }

  if (txData.value && txData.value.account_id && accounts.value.some((item) => item.id === txData.value.account_id)) {
    form.account_id = txData.value.account_id
    return
  }

  if (!accounts.value.some((item) => item.id === form.account_id)) {
    form.account_id = accounts.value[0].id
  }
}

async function loadTransaction() {
  const res = await api.get(endpoints.transactions, { limit: 500 })
  const tx = (res.transactions || []).find((item) => `${item.id}` === `${txId.value}`)
  if (!tx) {
    uni.showToast({ title: '未找到交易记录', icon: 'none' })
    return
  }

  txData.value = tx
  form.type = tx.type || 'expense'
  form.category = tx.category || ''
  form.date = tx.date || ''
  form.remark = tx.remark || ''
  form.account_id = tx.account_id || null
  form.currency = tx.currency || 'CNY'

  if (form.currency !== 'CNY' && tx.original_amount) {
    form.amount = `${tx.original_amount}`
  } else {
    form.amount = `${tx.amount || ''}`
  }

  typeIndex.value = form.type === 'expense' ? 0 : 1
}

onLoad(async (options) => {
  txId.value = options.id || ''
  try {
    await loadCategories()
    await loadTransaction()
    await loadAccounts()
  } catch (error) {
    showError(error, '加载交易失败')
  }
})

async function submit() {
  const amount = Number(form.amount || 0)
  if (!amount || amount <= 0) {
    return uni.showToast({ title: '金额不正确', icon: 'none' })
  }
  if (!form.category) {
    return uni.showToast({ title: '请选择分类', icon: 'none' })
  }
  if (!form.account_id) {
    return uni.showToast({ title: '请选择账户', icon: 'none' })
  }

  try {
    await api.put(`${endpoints.transactions}/${txId.value}`, {
      type: form.type,
      amount,
      category: form.category,
      date: form.date,
      remark: form.remark,
      account_id: form.account_id,
      currency: form.currency,
    })

    uni.showToast({ title: '更新成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 250)
  } catch (error) {
    showError(error, '更新失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.amount-input {
  font-size: 44rpx;
  font-weight: 700;
  height: 100rpx;
}

.picker {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 24rpx 22rpx 0;
  margin-bottom: 14rpx;
  background: #fff;
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
