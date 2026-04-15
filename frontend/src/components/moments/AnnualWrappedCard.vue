<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { AnnualWrappedData } from '@/types/micro'

const props = withDefaults(defineProps<{
  year: number
  force?: boolean
}>(), { force: false })

const visible = ref(false)

const wrapped = createResource({
  url: 'micro.api.moments.get_annual_wrapped',
  params: { year: props.year, force: props.force ? 1 : 0 },
  auto: true,
  transform(data: AnnualWrappedData) {
    if (data.should_show) {
      setTimeout(() => { visible.value = true }, 200)
    }
    return data
  },
})

const dismiss = createResource({
  url: 'micro.api.moments.dismiss_annual_wrapped',
  onSuccess() {
    visible.value = false
  },
})

function handleDismiss() {
  dismiss.submit({ year: props.year })
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value)
}

function exportPng() {
  const data = wrapped.data
  if (!data) return

  const w = 600
  const h = 520
  const canvas = document.createElement('canvas')
  canvas.width = w * 2   // 2x for retina
  canvas.height = h * 2
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.scale(2, 2)

  // Background
  ctx.fillStyle = '#ffffff'
  ctx.roundRect(0, 0, w, h, 16)
  ctx.fill()

  // Accent bar
  ctx.fillStyle = '#2563eb'
  ctx.roundRect(0, 0, w, 6, [16, 16, 0, 0])
  ctx.fill()

  // Title
  ctx.fillStyle = '#111827'
  ctx.font = 'bold 24px system-ui, -apple-system, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(`${__('Your {0} in Business').replace('{0}', String(data.year))}`, w / 2, 52)

  // Stats
  ctx.textAlign = 'left'
  const stats: [string, string][] = [
    [__('Offers sent'), String(data.offers_sent)],
    [__('Offers won'), `${data.offers_won}    (${data.win_rate}%)`],
    [__('Total pipeline value'), formatCurrency(data.pipeline_value)],
    [__('New clients'), String(data.new_clients)],
  ]

  if (data.projects_delivered !== null) {
    stats.push([__('Projects delivered'), String(data.projects_delivered)])
  }

  stats.push(
    [__('Best month'), `${__(data.best_month)} (${formatCurrency(data.best_month_value)})`],
    [__('Top client'), data.top_client_name],
  )

  let y = 100
  const labelX = 60
  const valueX = w - 60

  for (const [label, value] of stats) {
    // Separator line
    ctx.strokeStyle = '#f3f4f6'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(labelX, y - 8)
    ctx.lineTo(valueX, y - 8)
    ctx.stroke()

    ctx.fillStyle = '#6b7280'
    ctx.font = '14px system-ui, -apple-system, sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText(label, labelX, y + 8)

    ctx.fillStyle = '#111827'
    ctx.font = 'bold 16px system-ui, -apple-system, sans-serif'
    ctx.textAlign = 'right'
    ctx.fillText(value, valueX, y + 8)

    y += 42
  }

  // YoY growth
  if (data.yoy_growth_pct !== null) {
    y += 10
    ctx.fillStyle = data.yoy_growth_pct >= 0 ? '#059669' : '#dc2626'
    ctx.font = 'bold 18px system-ui, -apple-system, sans-serif'
    ctx.textAlign = 'center'
    const sign = data.yoy_growth_pct >= 0 ? '+' : ''
    ctx.fillText(
      __('You grew {0}% vs. {1}.').replace('{0}', `${sign}${data.yoy_growth_pct}`).replace('{1}', String(data.year - 1)),
      w / 2,
      y + 8,
    )
  }

  // Powered by Micro watermark
  ctx.fillStyle = '#9ca3af'
  ctx.font = '12px system-ui, -apple-system, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(`— ${__('powered by Micro')}`, w / 2, h - 20)

  // Download
  const link = document.createElement('a')
  link.download = `micro-wrapped-${data.year}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}
</script>

<template>
  <Transition
    enter-active-class="transition duration-500 ease-out"
    enter-from-class="opacity-0 translate-y-4"
    enter-to-class="opacity-100 translate-y-0"
  >
    <div
      v-if="wrapped.data?.should_show && visible"
      class="relative overflow-hidden rounded-xl border border-blue-200 bg-white shadow-sm"
    >
      <!-- Blue accent bar -->
      <div class="h-1.5 bg-blue-600" />

      <div class="p-6">
        <!-- Dismiss -->
        <button
          class="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
          :aria-label="__('Dismiss')"
          @click="handleDismiss"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <!-- Title -->
        <h2 class="mb-6 text-center text-xl font-bold text-gray-900">
          {{ __('Your {0} in Business').replace('{0}', String(wrapped.data.year)) }}
        </h2>

        <!-- Stats grid -->
        <div class="mx-auto max-w-lg divide-y divide-gray-100">
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('Offers sent') }}</span>
            <span class="text-sm font-semibold text-gray-900">{{ wrapped.data.offers_sent }}</span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('Offers won') }}</span>
            <span class="text-sm font-semibold text-gray-900">
              {{ wrapped.data.offers_won }}
              <span class="ml-1 text-xs font-normal text-gray-400">({{ wrapped.data.win_rate }}%)</span>
            </span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('Total pipeline value') }}</span>
            <span class="text-sm font-semibold text-gray-900">{{ formatCurrency(wrapped.data.pipeline_value) }}</span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('New clients') }}</span>
            <span class="text-sm font-semibold text-gray-900">{{ wrapped.data.new_clients }}</span>
          </div>
          <div v-if="wrapped.data.projects_delivered !== null" class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('Projects delivered') }}</span>
            <span class="text-sm font-semibold text-gray-900">{{ wrapped.data.projects_delivered }}</span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('Best month') }}</span>
            <span class="text-sm font-semibold text-gray-900">
              {{ __(wrapped.data.best_month) }}
              <span class="ml-1 text-xs font-normal text-gray-400">({{ formatCurrency(wrapped.data.best_month_value) }})</span>
            </span>
          </div>
          <div class="flex items-center justify-between py-3">
            <span class="text-sm text-gray-500">{{ __('Top client') }}</span>
            <span class="text-sm font-semibold text-gray-900">{{ wrapped.data.top_client_name }}</span>
          </div>
        </div>

        <!-- YoY growth -->
        <p
          v-if="wrapped.data.yoy_growth_pct !== null"
          class="mt-4 text-center text-sm font-semibold"
          :class="wrapped.data.yoy_growth_pct >= 0 ? 'text-green-600' : 'text-red-600'"
        >
          {{ __('You grew {0}% vs. {1}.').replace('{0}', `${wrapped.data.yoy_growth_pct >= 0 ? '+' : ''}${wrapped.data.yoy_growth_pct}`).replace('{1}', String(wrapped.data.year - 1)) }}
        </p>

        <!-- Footer: watermark + export -->
        <div class="mt-6 flex items-center justify-between border-t border-gray-100 pt-4">
          <span class="text-xs text-gray-400">{{ __('powered by Micro') }}</span>
          <button
            class="inline-flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            @click="exportPng"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {{ __('Share as Image') }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>
