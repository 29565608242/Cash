const TOKEN_KEY = 'cash_token'
const USER_KEY = 'cash_user'

export const store = {
  state: {
    token: '',
    user: null,
  },
}

export function bootstrapAuth() {
  try {
    store.state.token = uni.getStorageSync(TOKEN_KEY) || ''
    store.state.user = uni.getStorageSync(USER_KEY) || null
  } catch (error) {
    store.state.token = ''
    store.state.user = null
  }
}

export function setAuth(token, user) {
  store.state.token = token || ''
  store.state.user = user || null
  uni.setStorageSync(TOKEN_KEY, store.state.token)
  uni.setStorageSync(USER_KEY, store.state.user)
}

export function clearAuth() {
  store.state.token = ''
  store.state.user = null
  uni.removeStorageSync(TOKEN_KEY)
  uni.removeStorageSync(USER_KEY)
}

export function isAuthed() {
  return !!store.state.token
}
