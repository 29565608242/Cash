<template>
  <view class="page-wrap">
    <view class="card">
      <view class="title">线上记账小程序</view>
      <view class="text-muted" style="margin-top: 10rpx">版本 1.0.0</view>
      <view class="desc">
        基于 Flask + uni-app 构建，支持交易、账户、账本、预算、借贷、报销、周期账单、报表与 AI 智能记账。
      </view>
    </view>
  </view>
</template>

<script setup></script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.title {
  font-size: 34rpx;
  font-weight: 700;
}

.desc {
  margin-top: 16rpx;
  line-height: 1.8;
}
</style>
