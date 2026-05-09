<template>
  <view class="page-wrap">
    <view class="card">
      <input class="input" v-model="draft.name" placeholder="新账本名称" />
      <input class="input" v-model="draft.description" placeholder="账本描述（可选）" />
      <view class="btn-primary" @tap="createLedger">创建账本</view>
    </view>

    <view class="card">
      <input class="input" v-model="inviteCode" placeholder="输入邀请码加入账本" />
      <view class="btn-primary" @tap="joinByCode">加入账本</view>
    </view>

    <view class="card">
      <view class="row list-item" v-for="item in ledgers" :key="item.id">
        <view>
          <view>{{ item.name }}</view>
          <view class="text-muted">角色: {{ item.role }} · 成员: {{ item.member_count }}</view>
        </view>
        <view class="actions">
          <view class="btn-line" @tap="switchLedger(item.id)">切换</view>
          <view class="btn-line" @tap="goMembers(item.id)">成员</view>
          <view class="btn-line" @tap="removeLedger(item)">删除</view>
        </view>
      </view>
      <view v-if="!ledgers.length" class="text-muted">暂无账本</view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { confirmModal, showError } from '../../services/utils'

const ledgers = ref([])
const inviteCode = ref('')
const draft = reactive({
  name: '',
  description: '',
})

async function loadLedgers() {
  try {
    const res = await api.get(endpoints.ledgers)
    ledgers.value = res.ledgers || []
  } catch (error) {
    showError(error, '加载账本失败')
  }
}

async function createLedger() {
  if (!draft.name.trim()) return uni.showToast({ title: '请输入账本名称', icon: 'none' })
  try {
    await api.post(endpoints.ledgers, {
      name: draft.name.trim(),
      description: draft.description.trim(),
      currency: 'CNY',
    })
    draft.name = ''
    draft.description = ''
    await loadLedgers()
    uni.showToast({ title: '创建成功', icon: 'success' })
  } catch (error) {
    showError(error, '创建账本失败')
  }
}

async function switchLedger(id) {
  try {
    await api.post(`${endpoints.ledgers}/${id}/switch`, {})
    uni.showToast({ title: '已切换账本', icon: 'success' })
  } catch (error) {
    showError(error, '切换失败')
  }
}

function goMembers(id) {
  uni.navigateTo({ url: `/pages/ledger-members/index?ledger_id=${id}` })
}

async function removeLedger(item) {
  if (item.role !== 'manager') return uni.showToast({ title: '仅管理员可删除', icon: 'none' })
  const ok = await confirmModal(`确认删除账本「${item.name}」？`)
  if (!ok) return
  try {
    await api.del(`${endpoints.ledgers}/${item.id}`)
    await loadLedgers()
  } catch (error) {
    showError(error, '删除账本失败')
  }
}

async function joinByCode() {
  const code = inviteCode.value.trim()
  if (!code) return uni.showToast({ title: '请输入邀请码', icon: 'none' })
  try {
    await api.post('/api/ledgers/join', { code })
    inviteCode.value = ''
    await loadLedgers()
    uni.showToast({ title: '加入成功', icon: 'success' })
  } catch (error) {
    showError(error, '加入失败')
  }
}

onShow(loadLedgers)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';
</style>
