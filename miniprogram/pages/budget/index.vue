<template>
  <view class="page-wrap">
    <view class="card">
      <view class="row">
        <view>当前月份：{{ month }}</view>
        <view class="chip" v-if="budgetData.budget">预算已设置</view>
      </view>
      <view class="row" style="margin-top: 12rpx">
        <view>总支出：¥{{ formatMoney(budgetData.total_expense) }}</view>
        <view>预算：¥{{ formatMoney(budgetData.budget?.total_amount || 0) }}</view>
      </view>
      <view class="text-muted" v-if="budgetData.budget" style="margin-top: 10rpx">
        剩余 ¥{{ formatMoney(budgetData.budget.remaining) }} · {{ formatPercent(budgetData.budget.progress) }}
      </view>
    </view>

    <view class="card">
      <input class="input" v-model="draft.total_amount" type="digit" placeholder="总预算金额" />
      <input class="input" v-model="draft.remark" placeholder="备注（可选）" />
      <view class="btn-primary" @tap="saveBudget">保存预算</view>
    </view>

    <view class="card">
      <view class="section-title">预算列表</view>
      <view class="row list-item" v-for="item in budgetList" :key="item.id">
        <view>
          <view>{{ item.account_name }}</view>
          <view class="text-muted">¥{{ formatMoney(item.total_amount) }} · {{ item.remark || '无备注' }}</view>
        </view>
        <view class="btn-line" @tap="deleteBudget(item.id)">删除</view>
      </view>
      <view v-if="!budgetList.length" class="text-muted">暂无预算</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, formatMoney, formatPercent, monthString, showError } from '../../services/utils'

const month = ref(monthString())
const budgetData = reactive({
  total_expense: 0,
  budget: null,
})
const budgetList = ref([])
const draft = reactive({
  total_amount: '',
  remark: '',
})

async function loadData() {
  try {
    const current = await api.get(endpoints.budgetsCurrent)
    Object.assign(budgetData, current.data || { total_expense: 0, budget: null })
    const list = await api.get(endpoints.budgetsList)
    budgetList.value = list.budgets || []
    if (budgetData.budget) {
      draft.total_amount = `${budgetData.budget.total_amount}`
      draft.remark = budgetData.budget.remark || ''
    }
  } catch (error) {
    showError(error, '加载预算失败')
  }
}

async function saveBudget() {
  const amount = Number(draft.total_amount || 0)
  if (!amount || amount <= 0) return uni.showToast({ title: '请输入正确预算金额', icon: 'none' })
  try {
    await api.post(endpoints.budgets, {
      month: month.value,
      total_amount: amount,
      remark: draft.remark,
      account_id: null,
      category_items: [],
    })
    await loadData()
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (error) {
    showError(error, '保存预算失败')
  }
}

async function deleteBudget(id) {
  const ok = await confirmModal('确认删除该预算？')
  if (!ok) return
  try {
    await api.del(`${endpoints.budgets}/${id}`)
    await loadData()
  } catch (error) {
    showError(error, '删除预算失败')
  }
}

onShow(loadData)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.section-title {
  font-size: 30rpx;
  font-weight: 600;
}
</style>
