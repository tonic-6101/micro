<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { MicroSettings } from '@/types/micro'

// Direct fetch to /api/method/ — works in both Desk (window.frappe)
// and Dock SPA (no full Frappe client, only csrf_token on window).
function getCsrf(): string {
  return (
    (window as any).frappe?.csrf_token ??
    (window as any).csrf_token ??
    (window as any).dockBoot?.session?.csrf_token ??
    ''
  )
}

async function callApi(method: string, args: Record<string, unknown> = {}) {
  const res = await fetch('/api/method/' + method, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': getCsrf(),
    },
    body: JSON.stringify(args),
  })
  const json = await res.json()
  if (!res.ok) {
    throw new Error(json?.exc_type ?? 'Request failed')
  }
  return { message: json.message }
}

const loading = ref(true)
const error = ref<string | null>(null)
const settings = ref<MicroSettings | null>(null)
const customerCount = ref<number | null>(null)
const articleCount = ref<number | null>(null)

onMounted(async () => {
  try {
    const [settingsRes, customersRes, articlesRes] = await Promise.all([
      callApi('frappe.client.get', { doctype: 'Micro Settings' }),
      callApi('frappe.client.get_count', { doctype: 'Contact', filters: { micro_status: ['is', 'set'] } }),
      callApi('frappe.client.get_count', { doctype: 'Micro Article' }),
    ])
    settings.value = settingsRes.message
    customerCount.value = customersRes.message
    articleCount.value = articlesRes.message
  } catch (e: any) {
    error.value = e?.message ?? __('Failed to load settings')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div v-if="loading" class="py-12 text-center text-sm text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="error" class="py-12 text-center text-sm text-red-500 dark:text-red-400">
      {{ error }}
    </div>

    <div v-else-if="settings" class="space-y-6">
      <!-- Company Information -->
      <div class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400">
          {{ __('Company Information') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Company Name') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.company_name || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Email') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.company_email || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Phone') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.company_phone || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Address') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.company_address || '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Defaults -->
      <div class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400">
          {{ __('Defaults') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Currency') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.default_currency }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Language') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.default_language }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Monthly Capacity Hours') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.monthly_capacity_hours || 100 }}{{ __('h / month') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Usage & Limits -->
      <div class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400">
          {{ __('Usage & Limits') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Customers') }}</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-lg font-bold text-gray-900 dark:text-white">{{ customerCount ?? '—' }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                / {{ settings.customer_limit || __('unlimited') }}
              </span>
            </div>
            <div
              v-if="settings.customer_limit"
              class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
            >
              <div
                class="h-full rounded-full transition-all"
                :class="(customerCount || 0) >= settings.customer_limit ? 'bg-red-500' : 'bg-accent-600'"
                :style="{ width: Math.min(100, ((customerCount || 0) / settings.customer_limit) * 100) + '%' }"
              />
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Articles') }}</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-lg font-bold text-gray-900 dark:text-white">{{ articleCount ?? '—' }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                / {{ settings.article_limit || __('unlimited') }}
              </span>
            </div>
            <div
              v-if="settings.article_limit"
              class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
            >
              <div
                class="h-full rounded-full transition-all"
                :class="(articleCount || 0) >= settings.article_limit ? 'bg-red-500' : 'bg-accent-600'"
                :style="{ width: Math.min(100, ((articleCount || 0) / settings.article_limit) * 100) + '%' }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Tax Advisor -->
      <div class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400">
          {{ __('Tax Advisor') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Name') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.tax_advisor_name || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Email') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.tax_advisor_email || '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Compliance -->
      <div class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400">
          {{ __('Compliance (Zone 2)') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Watermark Text') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.draft_watermark_text || 'ENTWURF' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Disclaimer') }}</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ settings.draft_disclaimer || '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Edit link -->
      <div class="flex justify-end">
        <a
          href="/app/micro-settings"
          class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
        >
          {{ __('Edit in Desk') }} &rarr;
        </a>
      </div>
    </div>
  </div>
</template>
