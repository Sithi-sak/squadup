import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ui from '@nuxt/ui/vue-plugin'
import './styles/theme.css'
import './styles/main.css'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ui)

await useAuthStore().init()

app.mount('#app')
