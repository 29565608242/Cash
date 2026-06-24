const ENV_CONFIG = {
  development: {
    baseUrl: 'http://127.0.0.1:8080',
  },
  production: {
    baseUrl: 'https://example.com',
  },
}

const env = typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'production'
  ? 'production'
  : 'development'

export const appConfig = {
  ...ENV_CONFIG[env],
}

export function assetUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//i.test(path)) return path
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${appConfig.baseUrl}${normalized}`
}
