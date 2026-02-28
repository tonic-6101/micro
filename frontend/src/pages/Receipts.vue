<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroReceipt } from '@/types/micro'

const search = ref('')
const selectedCategory = ref('')
const page = ref(1)
const pageSize = 20

const categories = ['', 'Materials', 'Travel', 'Office', 'Food', 'Software', 'Services', 'Other']

const receipts = createResource({
  url: 'micro.api.receipts.get_receipts',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
    category: selectedCategory.value || undefined,
  },
  auto: true,
  transform(data: { receipts: MicroReceipt[]; total: number }) {
    return data
  },
})

watch([search, selectedCategory, page], () => {
  receipts.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      search: search.value,
      category: selectedCategory.value || undefined,
    },
  })
  receipts.reload()
})

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

const categoryColors: Record<string, string> = {
  Materials: 'bg-orange-100 text-orange-800',
  Travel: 'bg-blue-100 text-blue-800',
  Office: 'bg-purple-100 text-purple-800',
  Food: 'bg-yellow-100 text-yellow-800',
  Software: 'bg-indigo-100 text-indigo-800',
  Services: 'bg-teal-100 text-teal-800',
  Other: 'bg-gray-100 text-gray-700',
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Receipts') }}
      </h1>
      <a
        href="/app/micro-receipt/new"
        class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
      >
        {{ __('New Receipt') }}
      </a>
    </div>

    <!-- Filters -->
    <div class="mb-4 flex gap-3">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search by vendor...')"
        class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      />
      <select
        v-model="selectedCategory"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      >
        <option value="">{{ __('All Categories') }}</option>
        <option v-for="cat in categories.slice(1)" :key="cat" :value="cat">
          {{ __(cat) }}
        </option>
      </select>
    </div>

    <!-- Receipt list -->
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Date') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Vendor') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Description') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Category') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Amount') }}
            </th>
            <th class="px-4 py-3 text-center text-xs font-medium uppercase text-gray-500">
              {{ __('Exported') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="receipt in receipts.data?.receipts"
            :key="receipt.name"
            class="cursor-pointer hover:bg-gray-50"
            @click="$router.push(`/app/micro-receipt/${receipt.name}`)"
          >
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
              {{ receipt.receipt_date }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
              {{ receipt.vendor || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ receipt.description || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="categoryColors[receipt.category] || 'bg-gray-100 text-gray-700'"
              >
                {{ __(receipt.category) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
              {{ formatCurrency(receipt.amount) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-center text-sm">
              <span v-if="receipt.exported" class="text-green-600">&#10003;</span>
              <span v-else class="text-gray-300">—</span>
            </td>
          </tr>

          <tr v-if="receipts.loading">
            <td colspan="6" class="px-4 py-8 text-center text-sm text-gray-500">
              {{ __('Loading...') }}
            </td>
          </tr>

          <tr v-else-if="receipts.error">
            <td colspan="6" class="px-4 py-8 text-center text-sm text-red-500">
              {{ __('Failed to load receipts. Please try again.') }}
            </td>
          </tr>

          <tr v-else-if="!receipts.data?.receipts?.length">
            <td colspan="6" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ search ? __('No receipts match your search') : __('No receipts yet') }}</p>
              <a
                v-if="!search"
                href="/app/micro-receipt/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Add your first receipt') }} &rarr;
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="receipts.data?.total && receipts.data.total > pageSize"
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
        :disabled="page * pageSize >= receipts.data.total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page++"
      >
        {{ __('Next') }}
      </button>
    </div>
  </div>
</template>
