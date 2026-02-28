<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroCustomer } from '@/types/micro'

const router = useRouter()
const search = ref('')
const sourceFilter = ref('')
const page = ref(1)
const pageSize = 20

const sources = [
  'Manual', 'Google Ads', 'Facebook', 'Instagram', 'LinkedIn',
  'Email Campaign', 'Cold Call', 'Web Form', 'Organic Search',
  'Referral', 'Partner', 'Event', 'Import', 'Other',
]

const customers = createResource({
  url: 'micro.api.customers.get_customers',
  params: {
    page: page.value,
    page_size: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { customers: MicroCustomer[]; total: number }) {
    return data
  },
})

const filteredCustomers = computed(() => {
  if (!sourceFilter.value || !customers.data?.customers) return customers.data?.customers
  return customers.data.customers.filter(
    (c: MicroCustomer) => c.source === sourceFilter.value
  )
})

watch([search, page], () => {
  customers.update({
    params: {
      page: page.value,
      page_size: pageSize,
      search: search.value,
    },
  })
  customers.reload()
})

function openCustomer(name: string) {
  router.push(`/micro/customers/${name}`)
}

const statusClasses: Record<string, string> = {
  Potential: 'bg-blue-100 text-blue-800',
  Active: 'bg-green-100 text-green-800',
  Inactive: 'bg-gray-100 text-gray-600',
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Customers') }}
      </h1>
      <router-link
        to="/micro/customers/new"
        class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
      >
        {{ __('New Customer') }}
      </router-link>
    </div>

    <!-- Search & Filters -->
    <div class="mb-4 flex gap-3">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search customers...')"
        class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      />
      <select
        v-model="sourceFilter"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      >
        <option value="">{{ __('All Sources') }}</option>
        <option v-for="src in sources" :key="src" :value="src">
          {{ __(src) }}
        </option>
      </select>
    </div>

    <!-- Customer list -->
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Name') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Status') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Type') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Email') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Phone') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="customer in filteredCustomers"
            :key="customer.name"
            class="cursor-pointer hover:bg-gray-50"
            @click="openCustomer(customer.name)"
          >
            <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
              {{ customer.full_name }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="statusClasses[customer.status] || 'bg-gray-100 text-gray-600'"
              >
                {{ __(customer.status) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="customer.contact_type === 'Person' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
              >
                {{ __(customer.contact_type) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ customer.email || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ customer.phone || '—' }}
            </td>
          </tr>

          <tr v-if="customers.loading">
            <td colspan="5" class="px-4 py-8 text-center text-sm text-gray-500">
              {{ __('Loading...') }}
            </td>
          </tr>

          <tr v-else-if="customers.error">
            <td colspan="5" class="px-4 py-8 text-center text-sm text-red-500">
              {{ __('Failed to load customers. Please try again.') }}
            </td>
          </tr>

          <tr v-else-if="!filteredCustomers?.length">
            <td colspan="5" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ search || sourceFilter ? __('No customers match your search') : __('No customers yet') }}</p>
              <router-link
                v-if="!search"
                to="/micro/customers/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Create your first customer') }} &rarr;
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="customers.data?.total && customers.data.total > pageSize"
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
        :disabled="page * pageSize >= customers.data.total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page++"
      >
        {{ __('Next') }}
      </button>
    </div>
  </div>
</template>
