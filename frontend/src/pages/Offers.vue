<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroOfferDraft } from '@/types/micro'

const router = useRouter()
const search = ref('')
const page = ref(1)
const pageSize = 20

const offers = createResource({
  url: 'micro.api.offers.get_offers',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { offers: MicroOfferDraft[]; total: number }) {
    return data
  },
})

watch([search, page], () => {
  offers.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      search: search.value,
    },
  })
  offers.reload()
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

function openOffer(name: string) {
  router.push(`/micro/offers/${name}`)
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Offer Drafts') }}
      </h1>
      <a
        href="/app/micro-offer-draft/new"
        class="rounded-md bg-accent-600 px-3 py-2 text-sm font-medium text-white hover:bg-accent-700"
      >
        {{ __('New Offer Draft') }}
      </a>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search offer drafts...')"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      />
    </div>

    <!-- Offers list -->
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Reference') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Title') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Contact') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Date') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Status') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Total') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="offer in offers.data?.offers"
            :key="offer.name"
            class="cursor-pointer hover:bg-gray-50"
            @click="openOffer(offer.name)"
          >
            <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
              {{ offer.reference }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
              {{ offer.title || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ offer.contact }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ offer.date }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="statusColors[offer.status] || 'bg-gray-100 text-gray-700'"
              >
                {{ __(offer.status) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
              {{ formatCurrency(offer.total) }}
            </td>
          </tr>

          <tr v-if="offers.loading">
            <td colspan="6" class="px-4 py-8 text-center text-sm text-gray-500">
              {{ __('Loading...') }}
            </td>
          </tr>

          <tr v-else-if="offers.error">
            <td colspan="6" class="px-4 py-8 text-center text-sm text-red-500">
              {{ __('Failed to load offers. Please try again.') }}
            </td>
          </tr>

          <tr v-else-if="!offers.data?.offers?.length">
            <td colspan="6" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ search ? __('No offers match your search') : __('No offer drafts yet') }}</p>
              <a
                v-if="!search"
                href="/app/micro-offer-draft/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Create your first offer draft') }} &rarr;
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="offers.data?.total && offers.data.total > pageSize"
      class="mt-4 flex items-center justify-between"
    >
      <button
        :disabled="page <= 1"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page--"
      >
        {{ __('Previous') }}
      </button>
      <span class="text-sm text-gray-500">
        {{ __('Page') }} {{ page }}
      </span>
      <button
        :disabled="page * pageSize >= offers.data.total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page++"
      >
        {{ __('Next') }}
      </button>
    </div>
  </div>
</template>
