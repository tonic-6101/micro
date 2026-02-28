// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import Components from 'unplugin-vue-components/vite'
import * as LucideIcons from 'lucide-static'
import path from 'path'

function camelToDash(key: string): string[] {
  // With numbers: barChart2 -> bar-chart-2
  let withNumber = key.replace(/[A-Z0-9]/g, (m) => '-' + m.toLowerCase())
  if (withNumber.startsWith('-')) withNumber = withNumber.substring(1)
  // Without numbers: barChart2 -> bar-chart2
  let withoutNumber = key.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase())
  if (withoutNumber.startsWith('-')) withoutNumber = withoutNumber.substring(1)
  if (withNumber !== withoutNumber) return [withNumber, withoutNumber]
  return [withNumber]
}

function getIcons(): Record<string, string> {
  const icons: Record<string, string> = {}
  for (const [key, svg] of Object.entries(LucideIcons)) {
    if (key === 'default') continue
    if (typeof svg !== 'string') continue
    const processed = svg.includes('stroke-width')
      ? svg.replace(/stroke-width="2"/g, 'stroke-width="1.5"')
      : svg
    icons[key] = processed
    for (const dashKey of camelToDash(key)) {
      if (dashKey !== key) icons[dashKey] = processed
    }
  }
  return icons
}

const lucideIcons = getIcons()

export default defineConfig({
  plugins: [
    ...frappeui({
      lucideIcons: false,
      buildConfig: {
        indexHtmlPath: path.resolve(
          __dirname,
          '..',
          'micro',
          'www',
          'micro.html'
        ),
      },
    }),
    Components({
      resolvers: [
        IconsResolver({
          prefix: false,
          enabledCollections: ['lucide'],
        }),
      ],
    }),
    Icons({
      customCollections: {
        lucide: (name: string) => lucideIcons[name],
      },
    }),
    vue(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    include: ['frappe-ui'],
  },
})
