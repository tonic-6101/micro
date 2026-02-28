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
  params: { doctype: 'Micro Customer' },
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
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Settings') }}
      </h1>
      <a
        href="/app/micro-settings"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        {{ __('Edit in Desk') }}
      </a>
    </div>

    <div v-if="settings.loading" class="py-12 text-center text-sm text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="settings.data" class="space-y-6">
      <!-- Company Information -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
          {{ __('Company Information') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400">{{ __('Company Name') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900">
              {{ settings.data.company_name || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Email') }}</div>
            <div class="mt-1 text-sm text-gray-900">
              {{ settings.data.company_email || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Phone') }}</div>
            <div class="mt-1 text-sm text-gray-900">
              {{ settings.data.company_phone || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Address') }}</div>
            <div class="mt-1 text-sm text-gray-900">
              {{ settings.data.company_address || '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Defaults -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
          {{ __('Defaults') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400">{{ __('Currency') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900">
              {{ settings.data.default_currency }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Language') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900">
              {{ settings.data.default_language }}
            </div>
          </div>
        </div>
      </div>

      <!-- Usage & Limits -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
          {{ __('Usage & Limits') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400">{{ __('Customers') }}</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-lg font-bold text-gray-900">{{ customerCount.data ?? '—' }}</span>
              <span class="text-sm text-gray-500">
                / {{ settings.data.customer_limit || __('unlimited') }}
              </span>
            </div>
            <div
              v-if="settings.data.customer_limit"
              class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100"
            >
              <div
                class="h-full rounded-full transition-all"
                :class="(customerCount.data || 0) >= settings.data.customer_limit ? 'bg-red-500' : 'bg-gray-900'"
                :style="{ width: Math.min(100, ((customerCount.data || 0) / settings.data.customer_limit) * 100) + '%' }"
              />
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Articles') }}</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-lg font-bold text-gray-900">{{ articleCount.data ?? '—' }}</span>
              <span class="text-sm text-gray-500">
                / {{ settings.data.article_limit || __('unlimited') }}
              </span>
            </div>
            <div
              v-if="settings.data.article_limit"
              class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100"
            >
              <div
                class="h-full rounded-full transition-all"
                :class="(articleCount.data || 0) >= settings.data.article_limit ? 'bg-red-500' : 'bg-gray-900'"
                :style="{ width: Math.min(100, ((articleCount.data || 0) / settings.data.article_limit) * 100) + '%' }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Tax Advisor -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
          {{ __('Tax Advisor') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400">{{ __('Name') }}</div>
            <div class="mt-1 text-sm text-gray-900">
              {{ settings.data.tax_advisor_name || '—' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Email') }}</div>
            <div class="mt-1 text-sm text-gray-900">
              {{ settings.data.tax_advisor_email || '—' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Compliance -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
          {{ __('Compliance (Zone 2)') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-gray-400">{{ __('Watermark Text') }}</div>
            <div class="mt-1 text-sm font-medium text-gray-900">
              {{ settings.data.draft_watermark_text || 'ENTWURF' }}
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">{{ __('Disclaimer') }}</div>
            <div class="mt-1 text-sm text-gray-500">
              {{ settings.data.draft_disclaimer || '—' }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
