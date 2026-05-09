<template>
  <view class="page-wrap">
    <view class="card">
      <picker mode="selector" :range="typeOptions" :value="typeIndex" @change="onTypeChange">
        <view class="input">类型：{{ typeOptions[typeIndex] }}</view>
      </picker>
      <input class="input" v-model="form.counterparty" placeholder="对方名称" />
      <input class="input" v-model="form.amount" type="digit" placeholder="金额" />
      <input class="input" v-model="form.date" placeholder="日期 YYYY-MM-DD" />
      <input class="input" v-model="form.due_date" placeholder="到期日 YYYY-MM-DD（可选）" />
      <input class="input" v-model="form.remark" placeholder="备注（可选）" />
      <view class="btn-primary" @tap="submit">保存</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { api, endpoints } from '../../services/api'
import { showError, today } from '../../services/utils'

const typeOptions = ['借入(borrow)', '借出(lend)']
const typeIndex = ref(0)
const form = reactive({
  type: 'borrow',
  counterparty: '',
  amount: '',
  date: today(),
  due_date: '',
  remark: '',
})

function onTypeChange(e) {
  typeIndex.value = Number(e.detail.value || 0)
  form.type = typeIndex.value === 0 ? 'borrow' : 'lend'
}

async function submit() {
  if (!form.counterparty.trim()) return uni.showToast({ title: '请输入对方名称', icon: 'none' })
  const amount = Number(form.amount || 0)
  if (!amount || amount <= 0) return uni.showToast({ title: '请输入正确金额', icon: 'none' })
  try {
    await api.post(endpoints.loans, {
      type: form.type,
      counterparty: form.counterparty.trim(),
      amount,
      date: form.date,
      due_date: form.due_date || null,
      remark: form.remark,
    })
    uni.showToast({ title: '新增成功', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 250)
  } catch (error) {
    showError(error, '新增借贷失败')
  }
}
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
