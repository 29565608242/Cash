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

.uni-tabbar__label {
  font-size: 26rpx !important;
}

.uni-tabbar__icon {
  width: 44rpx !important;
  height: 44rpx !important;
}
</style>
