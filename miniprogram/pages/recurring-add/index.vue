<template>
  <view class="page-wrap">
    <view class="card">
      <input class="input" v-model="form.name" placeholder="规则名称" />
      <picker mode="selector" :range="typeOptions" :value="typeIndex" @change="onTypeChange">
        <view class="input">类型：{{ typeOptions[typeIndex] }}</view>
      </picker>
      <input class="input" v-model="form.amount" type="digit" placeholder="金额" />
      <input class="input" v-model="form.category" placeholder="分类名称（如 餐饮/工资）" />
      <picker mode="selector" :range="periodOptions" :value="periodIndex" @change="onPeriodChange">
        <view class="input">周期：{{ periodOptions[periodIndex] }}</view>
      </picker>
      <input class="input" v-model="form.interval_value" type="number" placeholder="间隔（默认1）" />
      <input class="input" v-model="form.start_date" placeholder="开始日期 YYYY-MM-DD" />
      <input class="input" v-model="form.end_date" placeholder="结束日期 YYYY-MM-DD（可选）" />
      <input class="input" v-model="form.remark" placeholder="备注（可选）" />
      <view class="btn-primary" @tap="submit">{{ ruleId ? '更新规则' : '创建规则' }}</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { showError, today } from '../../services/utils'

const ruleId = ref('')
const typeOptions = ['支出(expense)', '收入(income)']
const periodOptions = ['daily', 'weekly', 'monthly', 'yearly']
const typeIndex = ref(0)
const periodIndex = ref(2)

const form = reactive({
  name: '',
  type: 'expense',
  amount: '',
  category: '',
  period: 'monthly',
  interval_value: '1',
  start_date: today(),
  end_date: '',
  remark: '',
})

onLoad(async (options) => {
  ruleId.value = options.rule_id || ''
  if (ruleId.value) await loadRule(ruleId.value)
})

function onTypeChange(e) {
  typeIndex.value = Number(e.detail.value || 0)
  form.type = typeIndex.value === 0 ? 'expense' : 'income'
}

function onPeriodChange(e) {
  periodIndex.value = Number(e.detail.value || 0)
  form.period = periodOptions[periodIndex.value]
}

async function loadRule(id) {
  try {
    const res = await api.get(endpoints.recurringRules)
    const item = (res.rules || []).find((x) => `${x.id}` === `${id}`)
    if (!item) return
    form.name = item.name || ''
    form.type = item.type || 'expense'
    form.amount = `${item.amount || ''}`
    form.category = item.category || ''
    form.period = item.period || 'monthly'
    form.interval_value = `${item.interval_value || 1}`
    form.start_date = item.start_date || today()
    form.end_date = item.end_date || ''
    form.remark = item.remark || ''
    typeIndex.value = form.type === 'income' ? 1 : 0
    periodIndex.value = Math.max(0, periodOptions.indexOf(form.period))
  } catch (error) {
    showError(error, '加载规则失败')
  }
}

async function submit() {
  if (!form.name.trim()) return uni.showToast({ title: '请输入规则名称', icon: 'none' })
  if (!form.category.trim()) return uni.showToast({ title: '请输入分类', icon: 'none' })
  const amount = Number(form.amount || 0)
  if (!amount || amount <= 0) return uni.showToast({ title: '请输入正确金额', icon: 'none' })
  const payload = {
    name: form.name.trim(),
    type: form.type,
    amount,
    category: form.category.trim(),
    period: form.period,
    interval_value: Number(form.interval_value || 1),
    start_date: form.start_date,
    end_date: form.end_date || null,
    remark: form.remark,
  }
  try {
    if (ruleId.value) {
      await api.put(`${endpoints.recurringRules}/${ruleId.value}`, payload)
    } else {
      await api.post(endpoints.recurringRules, payload)
    }
    uni.showToast({ title: '保存成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 250)
  } catch (error) {
    showError(error, '保存失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
