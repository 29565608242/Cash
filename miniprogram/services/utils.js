export function formatMoney(value) {
  const num = Number(value || 0)
  return num.toFixed(2)
}

export function formatPercent(value) {
  const num = Number(value || 0)
  return `${num.toFixed(1)}%`
}

export function today() {
  const date = new Date()
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function nowTime() {
  const date = new Date()
  const h = `${date.getHours()}`.padStart(2, '0')
  const m = `${date.getMinutes()}`.padStart(2, '0')
  const s = `${date.getSeconds()}`.padStart(2, '0')
  return `${h}:${m}:${s}`
}

export function monthString() {
  const date = new Date()
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  return `${y}-${m}`
}

export function showError(error, fallback = '操作失败') {
  uni.showToast({
    title: (error && error.message) || fallback,
    icon: 'none',
  })
}

export function confirmModal(content, title = '提示') {
  return new Promise((resolve) => {
    uni.showModal({
      title,
      content,
      success: (res) => resolve(!!res.confirm),
      fail: () => resolve(false),
    })
  })
}

export function typeLabel(type) {
  if (type === 'income') return '收入'
  if (type === 'expense') return '支出'
  return type || '-'
}
