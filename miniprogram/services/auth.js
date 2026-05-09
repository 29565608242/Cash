import { api } from './api'
import { clearAuth, setAuth } from '../store/index'

export async function login(username, password) {
  const res = await api.post('/api/auth/login', { username, password }, false)
  setAuth(res.token, res.user)
  return res.user
}

export async function register(username, password, email = '') {
  const res = await api.post('/api/auth/register', { username, password, email }, false)
  setAuth(res.token, res.user)
  return res.user
}

export async function logout() {
  try {
    await api.post('/api/auth/logout', {})
  } catch (error) {}
  clearAuth()
}
