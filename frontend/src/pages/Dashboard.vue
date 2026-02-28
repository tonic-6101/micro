<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { DashboardKPIs } from '@/types/micro'

const kpis = createResource({
  url: 'micro.api.dashboard.get_dashboard_kpis',
  auto: true,
  transform(data: DashboardKPIs) {
    return data
  },
})

const sortedSources = computed(() => {
  if (!kpis.data?.customers?.by_source) return []
  return Object.entries(kpis.data.customers.by_source)
    .sort((a, b) => b[1] - a[1])
})

const sourceMaxCount = computed(() => {
  if (!sortedSources.value.length) return 1
  return sortedSources.value[0][1]
})

const sourceColors: Record<string, string> = {
  'Google Ads': 'bg-red-400',
  'Facebook': 'bg-blue-500',
  'Instagram': 'bg-pink-400',
  'LinkedIn': 'bg-sky-600',
  'Email Campaign': 'bg-violet-400',
  'Cold Call': 'bg-amber-400',
  'Web Form': 'bg-emerald-400',
  'Organic Search': 'bg-green-500',
  'Referral': 'bg-teal-400',
  'Partner': 'bg-indigo-400',
  'Event': 'bg-orange-400',
  'Manual': 'bg-gray-400',
  'Import': 'bg-slate-400',
  'Other': 'bg-gray-300',
  'Unknown': 'bg-gray-200',
}

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return __('just now')
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}

const doctypeLabels: Record<string, string> = {
  'Micro Customer': 'Customer',
  'Micro Offer Draft': 'Offer',
  'Micro Invoice Draft': 'Invoice Draft',
  'Micro Receipt': 'Receipt',
}
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold text-gray-900">
      {{ __('Dashboard') }}
    </h1>

    <div v-if="kpis.loading" class="py-12 text-center text-sm text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="kpis.data" class="space-y-6">
      <!-- Primary KPI Cards -->
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <p class="text-xs font-medium uppercase text-gray-500">{{ __('Customers') }}</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">
            {{ kpis.data.customers.total }}
          </p>
          <p v-if="kpis.data.customers.by_status" class="mt-0.5 text-xs text-gray-400">
            {{ kpis.data.customers.by_status.Potential || 0 }} {{ __('potential') }}
            · {{ kpis.data.customers.by_status.Active || 0 }} {{ __('active') }}
          </p>
        </div>

        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <p class="text-xs font-medium uppercase text-gray-500">{{ __('Offers') }}</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">
            {{ kpis.data.offers.total }}
          </p>
        </div>

        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <p class="text-xs font-medium uppercase text-gray-500">{{ __('Invoice Drafts') }}</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">
            {{ kpis.data.invoices.total }}
          </p>
        </div>

        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <p class="text-xs font-medium uppercase text-gray-500">{{ __('Receipts') }}</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">
            {{ kpis.data.receipts.total }}
          </p>
          <p class="mt-0.5 text-xs text-gray-400">
            {{ formatCurrency(kpis.data.receipts.total_amount) }}
          </p>
        </div>
      </div>

      <!-- Alerts -->
      <div
        v-if="kpis.data.receipts.unexported > 0"
        class="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3"
      >
        <span class="text-amber-600">!</span>
        <span class="text-sm text-amber-800">
          {{ kpis.data.receipts.unexported }}
          {{ __('receipts not yet exported to tax advisor') }}
        </span>
        <router-link
          to="/micro/export"
          class="ml-auto text-sm font-medium text-amber-700 hover:text-amber-900"
        >
          {{ __('Export now') }}
        </router-link>
      </div>

      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Recent Activity -->
        <div class="rounded-lg border border-gray-200 bg-white p-5">
          <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
            {{ __('Recent Activity') }}
          </h2>
          <div v-if="kpis.data.recent_activity.length" class="space-y-3">
            <div
              v-for="item in kpis.data.recent_activity.slice(0, 8)"
              :key="`${item.doctype}-${item.name}`"
              class="flex items-center justify-between"
            >
              <div class="flex items-center gap-2">
                <span
                  class="inline-flex rounded px-1.5 py-0.5 text-[10px] font-medium uppercase"
                  :class="{
                    'bg-blue-50 text-blue-700': item.doctype === 'Micro Customer',
                    'bg-purple-50 text-purple-700': item.doctype === 'Micro Offer Draft',
                    'bg-orange-50 text-orange-700': item.doctype === 'Micro Invoice Draft',
                    'bg-teal-50 text-teal-700': item.doctype === 'Micro Receipt',
                  }"
                >
                  {{ __(doctypeLabels[item.doctype] || item.doctype) }}
                </span>
                <span class="text-sm text-gray-900">{{ item.label }}</span>
              </div>
              <span class="text-xs text-gray-400">{{ timeAgo(item.modified) }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">
            {{ __('No recent activity') }}
          </p>
        </div>

        <!-- Customers by Source -->
        <div class="rounded-lg border border-gray-200 bg-white p-5">
          <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
            {{ __('Customers by Source') }}
          </h2>
          <div v-if="sortedSources.length" class="space-y-2.5">
            <div v-for="[source, count] in sortedSources" :key="source">
              <div class="mb-1 flex items-center justify-between">
                <span class="text-sm text-gray-700">{{ __(source) }}</span>
                <span class="text-sm font-medium text-gray-900">{{ count }}</span>
              </div>
              <div class="h-2 w-full overflow-hidden rounded-full bg-gray-100">
                <div
                  class="h-full rounded-full transition-all"
                  :class="sourceColors[source] || 'bg-gray-300'"
                  :style="{ width: `${(count / sourceMaxCount) * 100}%` }"
                />
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400">
            {{ __('No customers yet') }}
          </p>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h2 class="mb-4 text-sm font-medium uppercase text-gray-500">
          {{ __('Quick Actions') }}
        </h2>
        <div class="flex flex-wrap gap-2">
          <router-link
            to="/micro/customers/new"
            class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            {{ __('New Customer') }}
          </router-link>
          <a
            href="/app/micro-offer-draft/new"
            class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            {{ __('New Offer') }}
          </a>
          <a
            href="/app/micro-receipt/new"
            class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            {{ __('New Receipt') }}
          </a>
          <router-link
            to="/micro/export"
            class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            {{ __('Export to Tax Advisor') }}
          </router-link>
        </div>
      </div>

      <!-- Open Tasks -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-medium uppercase text-gray-500">
            {{ __('Open Tasks') }}
          </h2>
          <span class="text-2xl font-bold text-gray-900">
            {{ kpis.data.tasks.open }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
