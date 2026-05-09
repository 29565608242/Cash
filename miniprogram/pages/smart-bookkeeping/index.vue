<template>
  <view class="page-wrap">
    <view class="card">
      <textarea class="textarea" v-model="text" placeholder="输入自然语言，例如：昨天午饭花了35，今天工资到账8000" />
      <view class="btn-primary" @tap="parseText">智能解析</view>
    </view>

    <view class="card" v-if="parsedItems.length">
      <view class="section-title">解析结果</view>
      <view class="list-item" v-for="(item, idx) in parsedItems" :key="idx">
        <view class="row">
          <view>{{ item.type }} · {{ item.category }}</view>
          <view>¥{{ formatMoney(item.amount) }}</view>
        </view>
        <view class="text-muted">{{ item.date }} {{ item.time }}</view>
        <view class="text-muted">{{ item.remark }}</view>
        <view class="btn-line" style="margin-top: 8rpx" @tap="confirmOne(item)">确认入账</view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { api, endpoints } from '../../services/api'
import { formatMoney, showError } from '../../services/utils'

const text = ref('')
const parsedItems = ref([])

async function parseText() {
  const content = text.value.trim()
  if (!content) return uni.showToast({ title: '请输入记账文本', icon: 'none' })
  try {
    const res = await api.post(endpoints.smartParse, { text: content })
    if (res.multi) {
      parsedItems.value = res.parsed_list || []
    } else if (res.parsed) {
      parsedItems.value = [res.parsed]
    } else {
      parsedItems.value = []
    }
  } catch (error) {
    showError(error, '解析失败')
  }
}

async function confirmOne(item) {
  try {
    await api.post(endpoints.smartConfirm, item)
    uni.showToast({ title: '入账成功', icon: 'success' })
  } catch (error) {
    showError(error, '入账失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.section-title {
  font-size: 30rpx;
  font-weight: 600;
}
</style>
