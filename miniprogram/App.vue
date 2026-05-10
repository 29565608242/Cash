<script>
export default {
  onLaunch() {},
}
</script>

<style lang="scss">
@import './styles/variables.scss';
@import './styles/reset.scss';
@import './styles/components.scss';

page {
  background: $bg-page;
  color: $text-primary;
  font-size: 30rpx;
  line-height: 1.6;
}

/* Tab bar beautification */
.uni-tabbar {
  box-shadow: 0 -4rpx 20rpx rgba(67, 97, 238, 0.08) !important;
  border-top: none !important;
  backdrop-filter: blur(20rpx);
  -webkit-backdrop-filter: blur(20rpx);
  background: rgba(255, 255, 255, 0.92) !important;
}

.uni-tabbar__item {
  padding: 8rpx 0 4rpx !important;
  transition: all 0.2s ease;
}

.uni-tabbar__item.uni-tabbar__item_active .uni-tabbar__label {
  color: #4361EE !important;
  font-weight: 600;
  font-size: 24rpx !important;
}

.uni-tabbar__label {
  font-size: 22rpx !important;
  color: #9CA3AF !important;
  transition: color 0.2s ease;
}

.uni-tabbar__icon {
  width: 44rpx !important;
  height: 44rpx !important;
}
</style>
