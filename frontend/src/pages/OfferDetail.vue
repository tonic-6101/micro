<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CapacityWidget from '@/components/CapacityWidget.vue'
import type { MicroOfferDraft, MicroOfferItem } from '@/types/micro'

const props = defineProps<{
  id: string
}>()

const offer = createResource({
  url: 'micro.api.offers.get_offer',
  params: { offer_id: props.id },
  auto: true,
  transform(data: { offer: MicroOfferDraft }) {
    return data.offer
  },
})

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

const statusColors: Record<string, string> = {
  Draft: 'bg-gray-100 text-gray-700',
  Sent: 'bg-blue-100 text-blue-800',
  Accepted: 'bg-green-100 text-green-800',
  Declined: 'bg-red-100 text-red-800',
  Expired: 'bg-yellow-100 text-yellow-800',
}
</script>

<template>
  <div v-if="offer.loading" class="py-12 text-center text-sm text-gray-500">
    {{ __('Loading...') }}
  </div>

  <div v-else-if="offer.error" class="py-12 text-center">
    <p class="text-sm text-red-500">{{ __('Failed to load offer') }}</p>
    <router-link to="/micro/offers" class="mt-2 inline-block text-sm text-gray-500 hover:text-gray-700">
      &larr; {{ __('Back to Offer Drafts') }}
    </router-link>
  </div>

  <div v-else-if="offer.data">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3">
        <router-link
          to="/micro/offers"
          class="text-sm text-gray-500 hover:text-gray-700"
        >
          {{ __('Offer Drafts') }}
        </router-link>
        <span class="text-gray-300">/</span>
      </div>

      <div class="mt-2 flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">
            {{ offer.data.title || offer.data.reference }}
          </h1>
          <p class="mt-1 text-sm text-gray-500">{{ offer.data.reference }}</p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Watermark badge (G1 compliance) -->
          <span class="rounded-md bg-amber-50 px-3 py-1 text-sm font-bold text-amber-700 ring-1 ring-amber-200">
            {{ offer.data.watermark_text }}
          </span>
          <span
            class="inline-flex rounded-full px-3 py-1 text-sm font-medium"
            :class="statusColors[offer.data.status] || 'bg-gray-100 text-gray-700'"
          >
            {{ __(offer.data.status) }}
          </span>
          <a
            :href="`/app/micro-offer-draft/${offer.data.name}`"
            class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            {{ __('Edit in Desk') }}
          </a>
        </div>
      </div>
    </div>

    <!-- Capacity hint for draft/sent offers -->
    <CapacityWidget
      v-if="offer.data.status === 'Draft' || offer.data.status === 'Sent'"
      :compact="true"
      class="mb-4"
    />

    <!-- Meta cards -->
    <div class="mb-6 grid grid-cols-4 gap-4">
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Contact') }}</div>
        <div class="mt-1 text-sm font-medium text-gray-900">{{ offer.data.contact }}</div>
      </div>
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Date') }}</div>
        <div class="mt-1 text-sm text-gray-900">{{ offer.data.date }}</div>
      </div>
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Valid Until') }}</div>
        <div class="mt-1 text-sm text-gray-900">{{ offer.data.valid_until || '—' }}</div>
      </div>
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <div class="text-xs font-medium uppercase text-gray-500">{{ __('Total') }}</div>
        <div class="mt-1 text-lg font-bold text-gray-900">{{ formatCurrency(offer.data.total) }}</div>
      </div>
    </div>

    <!-- Items table -->
    <div class="mb-6 overflow-hidden rounded-lg border border-gray-200 bg-white">
      <div class="border-b border-gray-200 bg-gray-50 px-4 py-3">
        <h2 class="text-sm font-medium text-gray-700">{{ __('Items') }}</h2>
      </div>
      <table class="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Description') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Qty') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Unit') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Rate') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Amount') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="(item, idx) in (offer.data.items as MicroOfferItem[])" :key="idx">
            <td class="px-4 py-3 text-sm text-gray-900">{{ item.description }}</td>
            <td class="px-4 py-3 text-right text-sm text-gray-700">{{ item.quantity }}</td>
            <td class="px-4 py-3 text-sm text-gray-500">{{ item.unit || '' }}</td>
            <td class="px-4 py-3 text-right text-sm text-gray-700">{{ formatCurrency(item.rate) }}</td>
            <td class="px-4 py-3 text-right text-sm font-medium text-gray-900">{{ formatCurrency(item.amount) }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="border-t-2 border-gray-300">
            <td colspan="4" class="px-4 py-3 text-right text-sm font-medium text-gray-700">
              {{ __('Total') }}
            </td>
            <td class="px-4 py-3 text-right text-lg font-bold text-gray-900">
              {{ formatCurrency(offer.data.total) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Notes -->
    <div v-if="offer.data.notes" class="mb-6 rounded-lg border border-gray-200 bg-white p-4">
      <h2 class="mb-2 text-sm font-medium text-gray-700">{{ __('Notes for Client') }}</h2>
      <p class="text-sm text-gray-600">{{ offer.data.notes }}</p>
    </div>

    <!-- G4: Disclaimer (always shown) -->
    <div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-center">
      <p class="text-xs italic text-amber-700">{{ offer.data.disclaimer }}</p>
    </div>
  </div>
</template>
