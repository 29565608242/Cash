<template>
  <view class="page-wrap">
    <view class="card">
      <view class="row">
        <view>待报销 {{ summary.total_pending || 0 }}</view>
        <view>部分 {{ summary.total_partial || 0 }}</view>
        <view>已报销 {{ summary.total_reimbursed || 0 }}</view>
      </view>
    </view>

    <view class="card">
      <view class="row list-item" v-for="item in list" :key="item.id">
        <view>
          <view>{{ item.category }} · ¥{{ formatMoney(item.amount) }}</view>
          <view class="text-muted">{{ item.date }} · {{ item.reimbursement_status }}</view>
        </view>
        <view class="actions">
          <view class="btn-line" @tap="mark(item, 'pending')">待报销</view>
          <view class="btn-line" @tap="mark(item, 'reimbursed')">已报销</view>
          <view class="btn-line" @tap="writeOff(item)">核销</view>
        </view>
      </view>
      <view v-if="!list.length" class="text-muted">暂无报销记录</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { formatMoney, showError } from '../../services/utils'

const list = ref([])
const summary = reactive({
  total_pending: 0,
  total_partial: 0,
  total_reimbursed: 0,
})

async function loadData() {
  try {
    const res = await api.get(endpoints.reimbursements)
    list.value = res.reimbursements || []
    Object.assign(summary, res.summary || {})
  } catch (error) {
    showError(error, '加载报销失败')
  }
}

async function mark(item, status) {
  try {
    await api.put(`${endpoints.transactions}/${item.id}/reimbursement`, {
      reimbursement_status: status,
    })
    await loadData()
  } catch (error) {
    showError(error, '更新状态失败')
  }
}

async function writeOff(item) {
  const amountText = await new Promise((resolve) => {
    uni.showModal({
      title: '输入核销金额',
      editable: true,
      placeholderText: `${item.amount}`,
      success: (res) => resolve(res.confirm ? res.content : ''),
      fail: () => resolve(''),
    })
  })
  const amount = Number(amountText || 0)
  if (!amount || amount <= 0) return
  try {
    await api.post(`${endpoints.transactions}/${item.id}/write-off`, { amount })
    await loadData()
  } catch (error) {
    showError(error, '核销失败')
  }
}

onShow(loadData)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
