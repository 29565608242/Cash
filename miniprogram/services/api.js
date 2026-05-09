import { clearAuth, store } from '../store/index'

const BASE_URL = 'http://127.0.0.1:8080'

function request({ url, method = 'GET', data = null, auth = true, header = {} }) {
  return new Promise((resolve, reject) => {
    const headers = {
      'Content-Type': 'application/json',
      ...header,
    }

    if (auth && store.state.token) {
      headers.Authorization = `Bearer ${store.state.token}`
    }

    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      timeout: 15000,
      header: headers,
      success: (res) => {
        if (res.statusCode === 401) {
          clearAuth()
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期'))
          return
        }
        const payload = res.data || {}
        if (payload.success === false) {
          reject(new Error(payload.message || '请求失败'))
          return
        }
        resolve(payload)
      },
      fail: (err) => reject(err),
    })
  })
}

export const api = {
  request,
  get: (url, data, auth = true) => request({ url, method: 'GET', data, auth }),
  post: (url, data, auth = true) => request({ url, method: 'POST', data, auth }),
  put: (url, data, auth = true) => request({ url, method: 'PUT', data, auth }),
  del: (url, data, auth = true) => request({ url, method: 'DELETE', data, auth }),
}

export const endpoints = {
  auth: {
    login: '/api/auth/login',
    register: '/api/auth/register',
    logout: '/api/auth/logout',
  },
  user: {
    profile: '/api/user/profile',
    changePassword: '/api/user/change-password',
  },
  miniapp: {
    dashboard: '/api/miniapp/dashboard',
    upload: '/api/miniapp/upload',
  },
  transactions: '/api/transactions',
  categories: '/api/categories',
  accounts: '/api/accounts',
  ledgers: '/api/ledgers',
  budgetsCurrent: '/api/budgets/current',
  budgetsList: '/api/budgets/list',
  budgets: '/api/budgets',
  loans: '/api/loans',
  loanSummary: '/api/loans/summary',
  reimbursements: '/api/reimbursements',
  recurringRules: '/api/recurring-rules',
  recurringGenerate: '/api/recurring-rules/generate',
  report: (period) => `/api/reports/${period}`,
  reportAdvanced: '/api/reports/advanced',
  moneyChangeLogs: '/api/money-change-logs',
  smartParse: '/api/smart/parse',
  smartConfirm: '/api/smart/confirm',
  smartAI: '/api/smart/deepseek-analysis',
}
