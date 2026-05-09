<template>
  <view class="page-wrap">
    <view class="card">
      <view class="btn-primary" @tap="goCreate">新增规则</view>
      <view class="btn-primary" style="margin-top: 12rpx" @tap="generateNow">立即生成周期账单</view>
    </view>

    <view class="card">
      <view class="row list-item" v-for="item in rules" :key="item.id">
        <view>
          <view>{{ item.name }} · {{ item.period }}</view>
          <view class="text-muted">
            {{ item.type }} · ¥{{ formatMoney(item.amount) }} · 下次 {{ item.next_date }}
          </view>
        </view>
        <view class="actions">
          <view class="btn-line" @tap="toggle(item)">切换</view>
          <view class="btn-line" @tap="edit(item.id)">编辑</view>
          <view class="btn-line" @tap="removeRule(item.id)">删除</view>
        </view>
      </view>
      <view v-if="!rules.length" class="text-muted">暂无周期规则</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, formatMoney, showError } from '../../services/utils'

const rules = ref([])

function goCreate() {
  uni.navigateTo({ url: '/pages/recurring-add/index' })
}

function edit(id) {
  uni.navigateTo({ url: `/pages/recurring-add/index?rule_id=${id}` })
}

async function loadRules() {
  try {
    const res = await api.get(endpoints.recurringRules)
    rules.value = res.rules || []
  } catch (error) {
    showError(error, '加载规则失败')
  }
}

async function toggle(item) {
  try {
    await api.post(`${endpoints.recurringRules}/${item.id}/toggle`, {})
    await loadRules()
  } catch (error) {
    showError(error, '切换失败')
  }
}

async function generateNow() {
  try {
    const res = await api.post(endpoints.recurringGenerate, {})
    uni.showToast({ title: res.message || '已生成', icon: 'none' })
    await loadRules()
  } catch (error) {
    showError(error, '生成失败')
  }
}

async function removeRule(id) {
  const ok = await confirmModal('确认删除该周期规则？')
  if (!ok) return
  try {
    await api.del(`${endpoints.recurringRules}/${id}`)
    await loadRules()
  } catch (error) {
    showError(error, '删除失败')
  }
}

onShow(loadRules)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
