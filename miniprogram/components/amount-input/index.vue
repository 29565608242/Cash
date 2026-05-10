<template>
  <view class="amount-input">
    <input
      class="input"
      type="digit"
      :value="displayValue"
      :placeholder="placeholder"
      @input="onInput"
      @blur="onBlur"
    />
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  placeholder: {
    type: String,
    default: '请输入金额',
  },
})

const emit = defineEmits(['update:modelValue'])

const displayValue = computed(() => `${props.modelValue ?? ''}`)

function onInput(event) {
  emit('update:modelValue', event.detail.value || '')
}

function onBlur(event) {
  const raw = `${event.detail.value || ''}`.trim()
  if (!raw) return emit('update:modelValue', '')
  const num = Number(raw)
  if (Number.isFinite(num) && num >= 0) {
    emit('update:modelValue', num.toFixed(2))
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';

.amount-input {
  width: 100%;
}

.input {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 0 22rpx;
  background: #fff;
}
</style>
