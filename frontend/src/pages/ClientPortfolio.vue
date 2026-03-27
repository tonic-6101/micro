<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

interface PortfolioEntry {
  name: string
  full_name: string
  image?: string
  status: string
  contact_type: string
  health_score: string
  health_score_updated?: string
  lifetime_revenue: number
  referral_count: number
}

interface PortfolioInsights {
  total_contacts: number
  total_revenue: number
  a_client_count: number
  a_revenue_pct: number
  a_contact_pct: number
  grade_counts: Record<string, number>
}

interface PortfolioResponse {
  portfolio: PortfolioEntry[]
  insights: PortfolioInsights
}

const router = useRouter()

const portfolio = createResource({
  url: 'micro.api.health.get_client_portfolio',
  auto: true,
  transform(data: PortfolioResponse) {
    return data
  },
})

const recalcAll = createResource({
  url: 'micro.api.health.recalculate_score',
})

const gradeClasses: Record<string, string> = {
  A: 'bg-green-100 text-green-800 border-green-200',
  B: 'bg-blue-100 text-blue-800 border-blue-200',
  C: 'bg-amber-100 text-amber-800 border-amber-200',
  D: 'bg-red-100 text-red-800 border-red-200',
}

const gradeDots: Record<string, number> = {
  A: 5,
  B: 4,
  C: 3,
  D: 2,
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

function openCustomer(name: string) {
  router.push(`/micro/customers/${name}`)
}

const insightMessage = computed(() => {
  if (!portfolio.data?.insights) return ''
  const { a_revenue_pct, a_contact_pct } = portfolio.data.insights
  if (a_revenue_pct === 0 && a_contact_pct === 0) return ''
  return __('Your A-clients represent {pct}% of your revenue but only {contact_pct}% of your contacts. Focusing here is likely your highest-leverage move.')
    .replace('{pct}', String(a_revenue_pct))
    .replace('{contact_pct}', String(a_contact_pct))
})
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Client Portfolio') }}
      </h1>
    </div>

    <div v-if="portfolio.loading" class="py-12 text-center text-sm text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="portfolio.data" class="space-y-6">
      <!-- Grade summary cards -->
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div
          v-for="grade in ['A', 'B', 'C', 'D']"
          :key="grade"
          class="rounded-lg border bg-white p-4"
          :class="gradeClasses[grade]"
        >
          <p class="text-3xl font-bold">{{ grade }}</p>
          <p class="mt-1 text-sm">
            {{ portfolio.data.insights.grade_counts[grade] || 0 }}
            {{ __('Customers') }}
          </p>
        </div>
      </div>

      <!-- Insight message -->
      <div
        v-if="insightMessage"
        class="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800"
      >
        {{ insightMessage }}
      </div>

      <!-- Portfolio table -->
      <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                {{ __('Health Score') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                {{ __('Name') }}
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                {{ __('LTV') }}
              </th>
              <th class="px-4 py-3 text-center text-xs font-medium uppercase text-gray-500">
                {{ __('Referrals') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500" />
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr
              v-for="client in portfolio.data.portfolio"
              :key="client.name"
              class="cursor-pointer hover:bg-gray-50"
              @click="openCustomer(client.name)"
            >
              <td class="whitespace-nowrap px-4 py-3">
                <span
                  class="inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold"
                  :class="gradeClasses[client.health_score] || 'bg-gray-100 text-gray-500'"
                >
                  {{ client.health_score || '—' }}
                </span>
              </td>
              <td class="whitespace-nowrap px-4 py-3">
                <div class="flex items-center gap-3">
                  <img
                    v-if="client.image"
                    :src="client.image"
                    class="h-8 w-8 rounded-full object-cover"
                    alt=""
                  />
                  <div
                    v-else
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 text-xs font-medium text-gray-600"
                  >
                    {{ (client.full_name || '?')[0] }}
                  </div>
                  <span class="text-sm font-medium text-gray-900">{{ client.full_name }}</span>
                </div>
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-700">
                {{ formatCurrency(client.lifetime_revenue) }}
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-center text-sm text-gray-600">
                {{ client.referral_count }}
                {{ client.referral_count === 1 ? __('referral') : __('referrals') }}
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-400">
                <span class="flex gap-0.5">
                  <span
                    v-for="i in 5"
                    :key="i"
                    class="inline-block h-2 w-2 rounded-full"
                    :class="i <= (gradeDots[client.health_score] || 0) ? 'bg-gray-800' : 'bg-gray-200'"
                  />
                </span>
              </td>
            </tr>

            <tr v-if="!portfolio.data.portfolio.length">
              <td colspan="5" class="px-4 py-12 text-center text-sm text-gray-500">
                {{ __('No customers scored yet') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
