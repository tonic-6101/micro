// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

import { createApp } from 'vue'
import {
  FrappeUI,
  setConfig,
  frappeRequest,
  resourcesPlugin,
} from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './index.css'

setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(FrappeUI, { socketio: false })
app.use(resourcesPlugin)
app.use(router)
app.mount('#app')
