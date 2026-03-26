<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroSettings } from '@/types/micro'

const settings = createResource({
  url: 'frappe.client.get',
  params: { doctype: 'Micro Settings' },
  auto: true,
  transform(data: MicroSettings) {
    return data
  },
})

const customerCount = createResource({
  url: 'frappe.client.get_count',
  params: { doctype: 'Contact', filters: { micro_status: ['is', 'set'] } },
  auto: true,
})

const articleCount = createResource({
  url: 'frappe.client.get_count',
  params: { doctype: 'Micro Article' },
  auto: true,
})
</script>

<template>
  <div>
    <div v-if="settings.loading" class="py-12 text-center text-sm text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="settings.data" class="space-y-6">
      <!-- Company Information -->
      <div class="rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500 dark:text-gray-400">
          {{ __('Company Information') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Company Name') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.data.company_name || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Email') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.data.company_email || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Phone') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.data.company_phone || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Address') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.data.company_address || '—' }}
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
              {{ settings.data.default_currency }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Language') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.data.default_language }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Monthly Capacity Hours') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900 dark:text-white">
              {{ settings.data.monthly_capacity_hours || 100 }}{{ __('h / month') }}
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
              <span class="text-lg font-bold text-gray-900 dark:text-white">{{ customerCount.data ?? '—' }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                / {{ settings.data.customer_limit || __('unlimited') }}
              </span>
            </div>
            <div
              v-if="settings.data.customer_limit"
              class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
            >
              <div
                class="h-full rounded-full transition-all"
                :class="(customerCount.data || 0) >= settings.data.customer_limit ? 'bg-red-500' : 'bg-accent-600'"
                :style="{ width: Math.min(100, ((customerCount.data || 0) / settings.data.customer_limit) * 100) + '%' }"
              />
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Articles') }}</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-lg font-bold text-gray-900 dark:text-white">{{ articleCount.data ?? '—' }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                / {{ settings.data.article_limit || __('unlimited') }}
              </span>
            </div>
            <div
              v-if="settings.data.article_limit"
              class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-700"
            >
              <div
                class="h-full rounded-full transition-all"
                :class="(articleCount.data || 0) >= settings.data.article_limit ? 'bg-red-500' : 'bg-accent-600'"
                :style="{ width: Math.min(100, ((articleCount.data || 0) / settings.data.article_limit) * 100) + '%' }"
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
              {{ settings.data.tax_advisor_name || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Email') }}</div>
            <div class="mt-1 text-sm text-gray-900 dark:text-gray-200">
              {{ settings.data.tax_advisor_email || '—' }}
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
              {{ settings.data.draft_watermark_text || 'ENTWURF' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400 dark:text-gray-500">{{ __('Disclaimer') }}</div>
            <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {{ settings.data.draft_disclaimer || '—' }}
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
