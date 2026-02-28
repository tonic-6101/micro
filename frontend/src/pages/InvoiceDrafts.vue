<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroInvoiceDraft } from '@/types/micro'

const router = useRouter()
const search = ref('')
const page = ref(1)
const pageSize = 20

const invoices = createResource({
  url: 'micro.api.invoices.get_invoices',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { invoices: MicroInvoiceDraft[]; total: number }) {
    return data
  },
})

watch([search, page], () => {
  invoices.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      search: search.value,
    },
  })
  invoices.reload()
})

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

const statusColors: Record<string, string> = {
  Draft: 'bg-gray-100 text-gray-700',
  'Sent to Tax Advisor': 'bg-blue-100 text-blue-800',
  Archived: 'bg-green-100 text-green-800',
}

function openInvoice(name: string) {
  router.push(`/micro/invoice-drafts/${name}`)
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Invoice Drafts') }}
      </h1>
      <a
        href="/app/micro-invoice-draft/new"
        class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
      >
        {{ __('New Invoice Draft') }}
      </a>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search invoice drafts...')"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      />
    </div>

    <!-- Invoice list -->
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
              {{ __('Source') }}
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
            v-for="invoice in invoices.data?.invoices"
            :key="invoice.name"
            class="cursor-pointer hover:bg-gray-50"
            @click="openInvoice(invoice.name)"
          >
            <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
              {{ invoice.reference }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
              {{ invoice.title || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ invoice.contact }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ invoice.date }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ __(invoice.source) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="statusColors[invoice.status] || 'bg-gray-100 text-gray-700'"
              >
                {{ __(invoice.status) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
              {{ formatCurrency(invoice.total) }}
            </td>
          </tr>

          <tr v-if="invoices.loading">
            <td colspan="7" class="px-4 py-8 text-center text-sm text-gray-500">
              {{ __('Loading...') }}
            </td>
          </tr>

          <tr v-else-if="invoices.error">
            <td colspan="7" class="px-4 py-8 text-center text-sm text-red-500">
              {{ __('Failed to load invoice drafts. Please try again.') }}
            </td>
          </tr>

          <tr v-else-if="!invoices.data?.invoices?.length">
            <td colspan="7" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ search ? __('No invoice drafts match your search') : __('No invoice drafts yet') }}</p>
              <a
                v-if="!search"
                href="/app/micro-invoice-draft/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Create your first invoice draft') }} &rarr;
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="invoices.data?.total && invoices.data.total > pageSize"
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
        :disabled="page * pageSize >= invoices.data.total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page++"
      >
        {{ __('Next') }}
      </button>
    </div>
  </div>
</template>
