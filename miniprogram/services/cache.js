export function setCache(key, value) {
  uni.setStorageSync(key, value)
}

export function getCache(key, fallback = null) {
  const value = uni.getStorageSync(key)
  if (value === '' || value === undefined || value === null) {
    return fallback
  }
  return value
}

export function removeCache(key) {
  uni.removeStorageSync(key)
}
