<template>
  <view class="page-wrap">
    <view class="card">
      <picker mode="selector" :range="periodOptions" :value="periodIndex" @change="changePeriod">
        <view class="input">分析周期：{{ periodOptions[periodIndex] }}</view>
      </picker>
      <view class="btn-primary" @tap="loadAnalysis">生成 AI 分析</view>
    </view>

    <view class="card" v-if="result">
      <view class="section-title">AI 分析结果</view>
      <view class="text-muted" style="margin-top: 8rpx">
        区间：{{ result.start_date }} ~ {{ result.end_date }}
      </view>
      <view class="analysis">{{ result.analysis }}</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { api, endpoints } from '../../services/api'
import { showError } from '../../services/utils'

const periodOptions = ['week', 'month', 'quarter', 'year']
const periodIndex = ref(1)
const result = ref(null)

function changePeriod(e) {
  periodIndex.value = Number(e.detail.value || 0)
}

async function loadAnalysis() {
  try {
    const period = periodOptions[periodIndex.value]
    const res = await api.get(endpoints.smartAI, { period, force_refresh: true })
    result.value = res
  } catch (error) {
    showError(error, '获取分析失败')
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

.analysis {
  margin-top: 16rpx;
  white-space: pre-wrap;
  line-height: 1.7;
}
</style>
