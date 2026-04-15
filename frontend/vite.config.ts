// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import Components from 'unplugin-vue-components/vite'
import * as LucideIcons from 'lucide-static'
import path from 'path'
import fs from 'fs'
import { createRequire } from 'module'

const require = createRequire(import.meta.url)
const pkg = require('./package.json')

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

// Resolve any /assets/dock/* import as external — Dock's ESM bundle is
// served by Frappe at runtime, so Rollup must not try to resolve it.
const dockExternalPlugin: Plugin = {
  name: 'dock-external',
  enforce: 'pre',
  resolveId(id: string) {
    if (id.startsWith('/assets/dock/')) {
      return { id, external: true }
    }
  },
}

// Share Vue runtime with Dock so both use the same Vue instance,
// preventing dual-instance crashes.
// Only active during build — in dev mode Vue resolves normally from node_modules.
const vueSharedPlugin: Plugin = {
  name: 'vue-shared',
  enforce: 'pre',
  apply: 'build',
  resolveId(id: string) {
    if (id === 'vue' || id === '@vue/runtime-dom' || id === '@vue/runtime-core' || id === '@vue/reactivity') {
      return { id: '/assets/dock/js/vendor/vue.esm.js', external: true }
    }
    if (id === 'vue-router') {
      return { id: '/assets/dock/js/vendor/vue-router.esm.js', external: true }
    }
  },
}

// ── Settings ESM build ──────────────────────────────────────────────
// Builds micro-settings.esm.js — a standalone ESM bundle that exports
// MicroSettings component for Dock's unified settings hub.
// This runs as a secondary build after the main SPA build.
function settingsEsmPlugin(): Plugin {
  return {
    name: 'micro-settings-esm',
    async closeBundle() {
      const { build } = await import('vite')
      await build({
        configFile: false,
        base: '/assets/micro/js/',
        plugins: [
          vueSharedPlugin,
          vue(),
          ...frappeui({ frappeProxy: false, lucideIcons: true, jinjaBootData: false }),
        ],
        resolve: {
          alias: {
            '@': path.resolve(__dirname, 'src'),
          },
        },
        build: {
          outDir: path.resolve(__dirname, '../micro/public/js'),
          emptyOutDir: false,
          lib: {
            entry: path.resolve(__dirname, 'src/dock-settings.ts'),
            formats: ['es'],
            fileName: () => 'micro-settings.esm.js',
          },
          rollupOptions: {
            external: [
              'vue',
              'vue-router',
              '@vue/runtime-dom',
              '@vue/runtime-core',
              '@vue/reactivity',
              /^\/assets\/dock\//,
            ],
            output: {
              paths: {
                vue: '/assets/dock/js/vendor/vue.esm.js',
                'vue-router': '/assets/dock/js/vendor/vue-router.esm.js',
              },
            },
          },
        },
      })
      console.log('Built micro-settings.esm.js')
    },
  }
}

// Post-build: patch micro.html with Dock CSS, boot data, and dark-theme script.
// Runs after frappe-ui's build plugin generates the base HTML.
function microHtmlPlugin(): Plugin {
  return {
    name: 'micro-html-patch',
    closeBundle() {
      const htmlPath = path.resolve(__dirname, '..', 'micro', 'www', 'micro.html')
      if (!fs.existsSync(htmlPath)) return
      let html = fs.readFileSync(htmlPath, 'utf-8')

      // Add Dock CSS before the first <script> or <link> in <head>
      const dockCss = `    <link rel="stylesheet" href="/assets/dock/css/dock-tokens.css">\n    <link rel="stylesheet" href="/assets/dock/css/dock-navbar.css">\n`
      html = html.replace(
        /(<\s*script\b|<\s*link\b)/,
        dockCss + '    $1'
      )

      // Replace <body> contents with Dock-aware version
      html = html.replace(
        /<body>\s*<div id="app"><\/div>/,
        `<body>
    <script>
      // Prevent flash of wrong theme before Vue loads
      (function() {
        var stored = localStorage.getItem('dock-theme');
        var isDark = stored === 'dark' ||
          (!stored || stored === 'auto') && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (isDark) document.documentElement.classList.add('dark');
        var cm = localStorage.getItem('color-mode');
        if (cm === 'neutral') document.documentElement.setAttribute('data-color-mode', 'neutral');
      })();
    </script>
    <div id="app" class="h-screen"></div>
    <div id="modals"></div>
    <div id="popovers"></div>`
      )

      // Replace simple csrf_token script with full boot data
      html = html.replace(
        /\s*<script>\s*window\.csrf_token\s*=\s*"[^"]*";\s*<\/script>/,
        `
    <script>
      window.csrf_token = "{{ csrf_token }}";
    </script>
    {% for key in boot %}
    <script>
      window["{{ key }}"] = {{ boot[key] | tojson }};
    </script>
    {% endfor %}`
      )

      fs.writeFileSync(htmlPath, html)
      console.log('Patched micro.html with Dock integration')
    },
  }
}

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  plugins: [
    vueSharedPlugin,
    dockExternalPlugin,
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
    microHtmlPlugin(),
    settingsEsmPlugin(),
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
