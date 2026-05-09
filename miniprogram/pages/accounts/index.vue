<template>
  <view class="page-wrap">
    <view class="card">
      <input class="input" v-model="draft.name" placeholder="账户名称" />
      <picker mode="selector" :range="types" :value="typeIndex" @change="onTypeChange">
        <view class="input">账户类型：{{ types[typeIndex] }}</view>
      </picker>
      <input class="input" v-model="draft.balance" type="digit" placeholder="初始余额" />
      <view class="btn-primary" @tap="createAccount">新增账户</view>
    </view>

    <view class="card">
      <view class="row list-item" v-for="item in accounts" :key="item.id">
        <view>
          <view>{{ item.name }}</view>
          <view class="text-muted">{{ item.account_type }} · ¥{{ formatMoney(item.balance) }}</view>
        </view>
        <view class="actions">
          <view class="btn-line" @tap="editAccount(item)">编辑</view>
          <view class="btn-line" @tap="removeAccount(item.id)">删除</view>
        </view>
      </view>
      <view v-if="!accounts.length" class="text-muted">暂无账户</view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, formatMoney, showError } from '../../services/utils'

const accounts = ref([])
const types = ['cash', 'bank', 'credit', 'other']
const typeIndex = ref(0)
const draft = reactive({
  name: '',
  account_type: 'cash',
  balance: '0',
})

function onTypeChange(e) {
  typeIndex.value = Number(e.detail.value || 0)
  draft.account_type = types[typeIndex.value]
}

async function loadAccounts() {
  try {
    const res = await api.get(endpoints.accounts)
    accounts.value = res.accounts || []
  } catch (error) {
    showError(error, '加载账户失败')
  }
}

async function createAccount() {
  if (!draft.name.trim()) return uni.showToast({ title: '请输入账户名称', icon: 'none' })
  try {
    await api.post(endpoints.accounts, {
      name: draft.name.trim(),
      account_type: draft.account_type,
      balance: Number(draft.balance || 0),
    })
    draft.name = ''
    draft.balance = '0'
    await loadAccounts()
    uni.showToast({ title: '新增成功', icon: 'success' })
  } catch (error) {
    showError(error, '新增账户失败')
  }
}

async function editAccount(item) {
  const name = await new Promise((resolve) => {
    uni.showModal({
      title: '修改账户名',
      editable: true,
      placeholderText: item.name,
      content: item.name,
      success: (res) => resolve(res.confirm ? (res.content || '').trim() : ''),
      fail: () => resolve(''),
    })
  })
  if (!name) return
  try {
    await api.put(`${endpoints.accounts}/${item.id}`, {
      name,
      account_type: item.account_type,
      balance: Number(item.balance || 0),
    })
    await loadAccounts()
  } catch (error) {
    showError(error, '更新账户失败')
  }
}

async function removeAccount(id) {
  const ok = await confirmModal('确认删除该账户？')
  if (!ok) return
  try {
    await api.del(`${endpoints.accounts}/${id}`)
    await loadAccounts()
    uni.showToast({ title: '删除成功', icon: 'success' })
  } catch (error) {
    showError(error, '删除账户失败')
  }
}

onShow(loadAccounts)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
