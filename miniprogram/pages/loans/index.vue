<template>
  <view class="page-wrap">
    <view class="card">
      <view class="row">
        <view>总负债：¥{{ formatMoney(summary.total_borrow_remaining) }}</view>
        <view>总债权：¥{{ formatMoney(summary.total_lend_remaining) }}</view>
      </view>
      <view class="btn-primary" style="margin-top: 16rpx" @tap="goCreate">新增借贷</view>
    </view>

    <view class="card">
      <view class="row list-item" v-for="item in loans" :key="item.id">
        <view>
          <view>{{ item.type === 'borrow' ? '借入' : '借出' }} · {{ item.counterparty }}</view>
          <view class="text-muted">剩余 ¥{{ formatMoney(item.remaining) }} / 总额 ¥{{ formatMoney(item.amount) }}</view>
        </view>
        <view class="actions">
          <view class="btn-line" @tap="repay(item)">还款/收款</view>
          <view class="btn-line" @tap="removeLoan(item.id)">删除</view>
        </view>
      </view>
      <view v-if="!loans.length" class="text-muted">暂无借贷记录</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, formatMoney, showError } from '../../services/utils'

const loans = ref([])
const summary = reactive({
  total_borrow_remaining: 0,
  total_lend_remaining: 0,
})

function goCreate() {
  uni.navigateTo({ url: '/pages/loan-add/index' })
}

async function loadLoans() {
  try {
    const res = await api.get(endpoints.loans)
    loans.value = res.loans || []
    Object.assign(summary, res.summary || {})
  } catch (error) {
    showError(error, '加载借贷失败')
  }
}

async function repay(item) {
  const amountText = await new Promise((resolve) => {
    uni.showModal({
      title: item.type === 'borrow' ? '录入还款金额' : '录入收款金额',
      editable: true,
      placeholderText: '输入金额',
      success: (res) => resolve(res.confirm ? res.content : ''),
      fail: () => resolve(''),
    })
  })
  const amount = Number(amountText || 0)
  if (!amount || amount <= 0) return
  try {
    await api.post(`${endpoints.loans}/${item.id}/repay`, { amount })
    await loadLoans()
    uni.showToast({ title: '记录成功', icon: 'success' })
  } catch (error) {
    showError(error, '提交失败')
  }
}

async function removeLoan(id) {
  const ok = await confirmModal('确认删除该借贷记录？')
  if (!ok) return
  try {
    await api.del(`${endpoints.loans}/${id}`)
    await loadLoans()
  } catch (error) {
    showError(error, '删除失败')
  }
}

onShow(loadLoans)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
