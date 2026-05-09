<template>
  <view class="ledger-switcher">
    <picker mode="selector" :range="ledgerNames" :value="selectedIndex" @change="handleChange">
      <view class="picker-box">
        <text class="label">当前账本：</text>
        <text class="name">{{ currentName || '未选择' }}</text>
      </view>
    </picker>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../../services/api'

const props = defineProps({
  modelValue: {
    type: Number,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue', 'change'])

const ledgers = ref([])
const selectedIndex = ref(0)

const ledgerNames = computed(() => ledgers.value.map((item) => item.name))
const currentName = computed(() => ledgers.value[selectedIndex.value]?.name || '')

watch(
  () => props.modelValue,
  (value) => {
    if (value == null) return
    const idx = ledgers.value.findIndex((x) => x.id === value)
    if (idx >= 0) selectedIndex.value = idx
  },
  { immediate: true }
)

async function loadLedgers() {
  try {
    const res = await api.get('/api/ledgers')
    ledgers.value = res.ledgers || []
    if (!ledgers.value.length) return
    if (props.modelValue != null) {
      const idx = ledgers.value.findIndex((x) => x.id === props.modelValue)
      selectedIndex.value = idx >= 0 ? idx : 0
    } else {
      selectedIndex.value = 0
      emit('update:modelValue', ledgers.value[0].id)
    }
  } catch (error) {}
}

async function handleChange(event) {
  selectedIndex.value = Number(event.detail.value || 0)
  const current = ledgers.value[selectedIndex.value]
  if (!current) return
  try {
    await api.post(`/api/ledgers/${current.id}/switch`, {})
    emit('update:modelValue', current.id)
    emit('change', current)
  } catch (error) {}
}

loadLedgers()
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';

.ledger-switcher {
  width: 100%;
}

.picker-box {
  border: 1px solid $border;
  border-radius: $radius-md;
  padding: 16rpx 20rpx;
  background: #fff;
}

.label {
  color: $text-secondary;
  font-size: 24rpx;
}

.name {
  font-weight: 600;
  margin-left: 8rpx;
}
</style>
