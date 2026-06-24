<template>
  <view class="profile-page">
    <view class="profile-hero">
      <view class="hero-icons">
        <text class="scan" @tap="showPending('扫一扫')">□</text>
        <view class="right-icons">
          <text @tap="showPending('消息通知')">铃</text>
          <text @tap="showSettings">设</text>
        </view>
      </view>
      <text class="hero-title">个人中心</text>
      <view class="user-row">
        <view class="avatar-wrap" @tap="changeAvatar">
          <image v-if="avatarSource" class="avatar-img" :src="avatarSource" mode="aspectFill" />
          <view v-else class="avatar">{{ userInitial }}</view>
        </view>
        <view class="user-meta">
          <text class="name">{{ displayName }}</text>
          <text class="slogan">今天也适合记一笔</text>
        </view>
        <text class="hero-arrow" @tap="editProfile">›</text>
      </view>
    </view>

    <view class="feature-card vip-card" @tap="go('/pages/ai-analysis/index')">
      <text class="feature-icon gold">AI</text>
      <text class="feature-title">AI 消费洞察</text>
      <text class="feature-desc">查看收支分析</text>
      <text class="feature-arrow">›</text>
    </view>

    <view class="feature-card" @tap="go('/pages/reports/index')">
      <text class="feature-icon red">年</text>
      <text class="feature-title">年度总结</text>
      <text class="feature-desc">按时间生成账本报告</text>
      <text class="feature-arrow">›</text>
    </view>

    <view class="menu-group">
      <view class="menu-item" @tap="go('/pages/accounts/index')">
        <text class="menu-icon">卡</text>
        <text class="menu-title">资金账户</text>
        <text class="menu-desc">与当前账本联动</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item" @tap="go('/pages/smart-bookkeeping/index')">
        <text class="menu-icon">AI</text>
        <text class="menu-title">AI 自动记账</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item" @tap="go('/pages/ledger-members/index')">
        <text class="menu-icon">员</text>
        <text class="menu-title">账本成员</text>
        <text class="menu-desc">邀请与授权</text>
        <text class="feature-arrow">›</text>
      </view>
    </view>

    <view class="menu-group">
      <view class="menu-item" @tap="shareApp">
        <text class="menu-icon">享</text>
        <text class="menu-title">分享给朋友</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item" @tap="chooseImportFile">
        <text class="menu-icon">入</text>
        <text class="menu-title">导入账单</text>
        <text class="menu-desc">CSV / Excel</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item" @tap="openBrowserImport">
        <text class="menu-icon">网</text>
        <text class="menu-title">通过浏览器导入</text>
        <text class="menu-desc">高级字段映射</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item" @tap="exportBills">
        <text class="menu-icon">出</text>
        <text class="menu-title">导出账单</text>
        <text class="menu-desc">Excel 文件</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item" @tap="go('/pages/recurring/index')">
        <text class="menu-icon">醒</text>
        <text class="menu-title">记账提醒</text>
        <text class="menu-desc">周期账单与提醒</text>
        <text class="feature-arrow">›</text>
      </view>
    </view>

    <view v-if="importResult" class="status-panel">
      <text class="status-title">最近导入</text>
      <text class="status-desc">
        成功 {{ importResult.imported || 0 }} 条，跳过 {{ importResult.skipped || 0 }} 条
      </text>
    </view>

    <view v-if="exportTask" class="status-panel">
      <text class="status-title">最近导出</text>
      <text class="status-desc">
        {{ exportTask.statusText }} · {{ exportTask.total_records || 0 }} 条
      </text>
      <text v-if="exportTask.download_url" class="status-action" @tap="downloadExport(exportTask.download_url)">
        打开文件
      </text>
    </view>

    <view class="menu-group">
      <view class="menu-item" @tap="showPasswordPanel = !showPasswordPanel">
        <text class="menu-icon">密</text>
        <text class="menu-title">修改密码</text>
        <text class="feature-arrow">›</text>
      </view>
      <view v-if="showPasswordPanel" class="inline-form">
        <input class="input" v-model="password.old_password" type="password" placeholder="旧密码" />
        <input class="input" v-model="password.new_password" type="password" placeholder="新密码（至少6位）" />
        <view class="btn-primary" @tap="changePassword">保存新密码</view>
      </view>
      <view class="menu-item" @tap="go('/pages/about/index')">
        <text class="menu-icon">关</text>
        <text class="menu-title">关于系统</text>
        <text class="feature-arrow">›</text>
      </view>
      <view class="menu-item danger" @tap="doLogout">
        <text class="menu-icon">退</text>
        <text class="menu-title">退出登录</text>
      </view>
    </view>

    <view v-if="showProfileEditor" class="editor-mask" @tap="showProfileEditor = false">
      <view class="editor-panel" @tap.stop>
        <text class="editor-title">编辑资料</text>
        <input class="input" v-model="form.nickname" placeholder="昵称" />
        <input class="input" v-model="form.email" placeholder="邮箱" />
        <input class="input" v-model="form.phone" placeholder="手机号" />
        <view class="editor-actions">
          <view class="btn-cancel" @tap="showProfileEditor = false">取消</view>
          <view class="btn-primary save-profile" @tap="saveProfile">保存</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api, endpoints } from '../../services/api'
import { logout } from '../../services/auth'
import { store } from '../../store/index'
import { assetUrl } from '../../config/index'

const form = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  avatar: '',
})

const password = reactive({
  old_password: '',
  new_password: '',
})

const showProfileEditor = ref(false)
const showPasswordPanel = ref(false)
const importResult = ref(null)
const exportTask = ref(null)

const displayName = computed(() => form.nickname || form.username || '未登录用户')
const userInitial = computed(() => (displayName.value || 'U').slice(0, 1).toUpperCase())
const avatarSource = computed(() => {
  if (!form.avatar || form.avatar === 'default_avatar.svg' || form.avatar === 'default_avatar.png') return ''
  if (/^https?:\/\//i.test(form.avatar)) return form.avatar
  return assetUrl(form.avatar.startsWith('/static/') ? form.avatar : `/static/avatars/${form.avatar}`)
})

function go(url) {
  uni.navigateTo({ url })
}

function showPending(name) {
  uni.showToast({ title: `${name}即将接入`, icon: 'none' })
}

function showSettings() {
  showProfileEditor.value = true
}

function editProfile() {
  showProfileEditor.value = true
}

async function changeAvatar() {
  uni.chooseImage({
    count: 1,
    success: async (res) => {
      const tempPath = res.tempFilePaths[0]
      uni.showLoading({ title: '上传中...' })
      try {
        const data = await api.upload({
          url: endpoints.miniapp.upload,
          filePath: tempPath,
        })
        if (data.file && data.file.name) {
          form.avatar = data.file.name
          await api.put(endpoints.user.profile, { avatar: data.file.name })
          uni.showToast({ title: '头像已更新', icon: 'success' })
        } else {
          uni.showToast({ title: data.message || '上传失败', icon: 'none' })
        }
      } catch (error) {
        uni.showToast({ title: error.message || '上传失败', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    },
  })
}

async function loadProfile() {
  try {
    const res = await api.get(endpoints.user.profile)
    const user = res.user || {}
    form.username = user.username || ''
    form.nickname = user.nickname || ''
    form.email = user.email || ''
    form.phone = user.phone || ''
    form.avatar = user.avatar || ''
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
}

async function saveProfile() {
  try {
    await api.put(endpoints.user.profile, {
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
    })
    store.state.user = { ...(store.state.user || {}), ...form }
    showProfileEditor.value = false
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '保存失败', icon: 'none' })
  }
}

function chooseImportFile() {
  const handleFiles = (files = []) => {
    const file = files[0]
    if (!file || !file.path) {
      openBrowserImport()
      return
    }
    importBillFile(file.path)
  }

  if (uni.chooseMessageFile) {
    uni.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['csv', 'xlsx', 'xls'],
      success: (res) => handleFiles(res.tempFiles || []),
      fail: () => openBrowserImport(),
    })
    return
  }

  if (uni.chooseFile) {
    uni.chooseFile({
      count: 1,
      extension: ['.csv', '.xlsx', '.xls'],
      success: (res) => handleFiles(res.tempFiles || []),
      fail: () => openBrowserImport(),
    })
    return
  }

  openBrowserImport()
}

async function importBillFile(filePath) {
  uni.showLoading({ title: '解析账单...' })
  try {
    const upload = await api.upload({
      url: endpoints.importUpload,
      filePath,
      name: 'file',
    })
    const mapping = upload.auto_mapping || {}
    const missing = ['type', 'amount', 'category', 'date'].filter((key) => !mapping[key])
    if (missing.length) {
      uni.hideLoading()
      uni.showModal({
        title: '需要手动映射',
        content: '该文件列名无法自动识别，请使用浏览器导入完成字段映射。',
        confirmText: '打开链接',
        success: (res) => {
          if (res.confirm) openBrowserImport()
        },
      })
      return
    }

    const result = await api.post(endpoints.importConfirm, {
      upload_id: upload.upload_id,
      mapping,
      skip_errors: true,
    })
    importResult.value = result
    uni.showToast({ title: `导入 ${result.imported || 0} 条`, icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '导入失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

function openBrowserImport() {
  const url = assetUrl('/data')
  if (typeof window !== 'undefined' && window.location) {
    window.location.href = url
    return
  }
  uni.setClipboardData({
    data: url,
    success: () => {
      uni.showModal({
        title: '链接已复制',
        content: '请在手机浏览器打开该链接，使用完整的导入映射功能。',
        showCancel: false,
      })
    },
  })
}

async function exportBills() {
  uni.showLoading({ title: '生成导出...' })
  try {
    const data = await api.post(endpoints.exportCreate, {
      format: 'xlsx',
      account_id: null,
    })
    exportTask.value = {
      ...data,
      statusText: data.sync ? '已完成' : '生成中',
    }
    if (data.download_url) {
      await downloadExport(data.download_url)
      return
    }
    await pollExport(data.task_id)
  } catch (error) {
    uni.showToast({ title: error.message || '导出失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

async function pollExport(taskId) {
  if (!taskId) return
  for (let i = 0; i < 18; i += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1500))
    const data = await api.get(endpoints.exportStatus(taskId))
    exportTask.value = {
      ...data,
      statusText: data.status === 'completed'
        ? '已完成'
        : data.status === 'failed'
          ? '失败'
          : '生成中',
    }
    if (data.status === 'completed' && data.download_url) {
      await downloadExport(data.download_url)
      return
    }
    if (data.status === 'failed') {
      throw new Error(data.error_message || '导出失败')
    }
  }
  uni.showToast({ title: '导出仍在生成，可稍后再试', icon: 'none' })
}

function downloadExport(downloadUrl) {
  return new Promise((resolve) => {
    const url = assetUrl(downloadUrl)
    const header = store.state.token ? { Authorization: `Bearer ${store.state.token}` } : {}
    uni.downloadFile({
      url,
      header,
      success: (res) => {
        if (res.statusCode === 200 && res.tempFilePath) {
          if (uni.openDocument) {
            uni.openDocument({
              filePath: res.tempFilePath,
              showMenu: true,
              success: () => {
                uni.showToast({ title: '导出完成', icon: 'success' })
                resolve()
              },
              fail: () => copyExportLink(url, resolve),
            })
            return
          }
        }
        copyExportLink(url, resolve)
      },
      fail: () => copyExportLink(url, resolve),
    })
  })
}

function copyExportLink(url, done) {
  uni.setClipboardData({
    data: url,
    success: () => uni.showToast({ title: '下载链接已复制', icon: 'none' }),
    complete: () => done && done(),
  })
}

function shareApp() {
  if (uni.showShareMenu) {
    uni.showShareMenu({ withShareTicket: true })
  }
  uni.showToast({ title: '可使用右上角分享', icon: 'none' })
}

async function changePassword() {
  if (!password.old_password || !password.new_password) {
    uni.showToast({ title: '请输入完整密码信息', icon: 'none' })
    return
  }
  if (password.new_password.length < 6) {
    uni.showToast({ title: '新密码至少 6 位', icon: 'none' })
    return
  }
  try {
    await api.post(endpoints.user.changePassword, password)
    password.old_password = ''
    password.new_password = ''
    showPasswordPanel.value = false
    uni.showToast({ title: '密码修改成功', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error.message || '修改失败', icon: 'none' })
  }
}

async function doLogout() {
  await logout()
  uni.reLaunch({ url: '/pages/login/index' })
}

onShow(loadProfile)
</script>

<style lang="scss" scoped>
@import '../../styles/variables.scss';
@import '../../styles/components.scss';

.profile-page {
  min-height: 100vh;
  padding-bottom: 34rpx;
  background: #f3f6f8;
}

.profile-hero {
  padding: 56rpx 30rpx 42rpx;
  color: #fff;
  background: linear-gradient(135deg, #25d3de 0%, #0d98da 100%);
}

.hero-icons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 32rpx;
}

.right-icons {
  display: flex;
  gap: 34rpx;
}

.hero-title {
  display: block;
  margin-top: 6rpx;
  text-align: center;
  font-size: 44rpx;
  font-weight: 800;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-top: 44rpx;
}

.avatar-wrap,
.avatar-img,
.avatar {
  width: 94rpx;
  height: 94rpx;
  border-radius: 47rpx;
}

.avatar-img {
  background: rgba(255, 255, 255, 0.26);
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  font-size: 40rpx;
  font-weight: 800;
}

.user-meta {
  flex: 1;
}

.name {
  display: block;
  font-size: 34rpx;
  font-weight: 800;
}

.slogan {
  display: block;
  margin-top: 6rpx;
  font-size: 28rpx;
  opacity: 0.88;
}

.hero-arrow {
  font-size: 64rpx;
  font-weight: 300;
}

.feature-card,
.menu-group,
.status-panel {
  margin: 22rpx 24rpx;
  background: #fff;
  border-radius: 18rpx;
  box-shadow: 0 10rpx 24rpx rgba(18, 84, 110, 0.06);
}

.feature-card {
  min-height: 108rpx;
  padding: 0 26rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.vip-card {
  margin-top: 28rpx;
}

.feature-icon,
.menu-icon {
  width: 44rpx;
  color: #23add0;
  font-size: 28rpx;
  font-weight: 800;
}

.feature-icon.gold {
  color: #c7963a;
}

.feature-icon.red {
  color: #e7425d;
}

.feature-title,
.menu-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 800;
}

.feature-desc,
.menu-desc {
  margin-left: auto;
  color: #7f8b96;
  font-size: 26rpx;
}

.feature-arrow {
  color: #c9d0d6;
  font-size: 50rpx;
  line-height: 1;
}

.menu-item {
  min-height: 106rpx;
  padding: 0 26rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  border-bottom: 1px solid #edf1f4;
}

.menu-item:last-child {
  border-bottom: 0;
}

.menu-item.danger .menu-title,
.menu-item.danger .menu-icon {
  color: #e04f5f;
}

.status-panel {
  min-height: 92rpx;
  padding: 18rpx 26rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.status-title {
  color: #0f3c5c;
  font-size: 30rpx;
  font-weight: 800;
}

.status-desc {
  flex: 1;
  color: #7f8b96;
  font-size: 26rpx;
}

.status-action {
  color: #20acd1;
  font-size: 28rpx;
  font-weight: 700;
}

.inline-form {
  padding: 4rpx 26rpx 26rpx 88rpx;
  border-bottom: 1px solid #edf1f4;
}

.input {
  height: 84rpx;
  border: 1px solid $border;
  border-radius: 12rpx;
  padding: 0 22rpx;
  margin-bottom: 14rpx;
  background: #fff;
  font-size: 28rpx;
}

.editor-mask {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.38);
  z-index: 20;
}

.editor-panel {
  width: 100%;
  padding: 30rpx 30rpx 42rpx;
  border-radius: 24rpx 24rpx 0 0;
  background: #fff;
}

.editor-title {
  display: block;
  margin-bottom: 22rpx;
  color: #111827;
  font-size: 36rpx;
  font-weight: 800;
}

.editor-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.btn-cancel,
.save-profile {
  height: 82rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-cancel {
  color: #607080;
  background: #f1f3f5;
}

.save-profile {
  padding: 0;
}
</style>
