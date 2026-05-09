import App from './App'
import { createSSRApp } from 'vue'
import { bootstrapAuth } from './store/index'

export function createApp() {
  bootstrapAuth()
  const app = createSSRApp(App)
  return { app }
}
