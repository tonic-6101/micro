<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CapacityWidget from '@/components/CapacityWidget.vue'
import type { CustomerDetailResponse } from '@/types/micro'

const props = defineProps<{
  id: string
}>()

const customer = createResource({
  url: 'micro.api.customers.get_customer',
  params: { customer_id: props.id },
  auto: true,
  transform(data: CustomerDetailResponse) {
    return data
  },
})

const statusClasses: Record<string, string> = {
  Potential: 'bg-blue-100 text-blue-800',
  Active: 'bg-green-100 text-green-800',
  Inactive: 'bg-gray-100 text-gray-600',
}
</script>

<template>
  <div v-if="customer.loading" class="py-12 text-center text-sm text-gray-500">
    {{ __('Loading...') }}
  </div>

  <div v-else-if="customer.error" class="py-12 text-center">
    <p class="text-sm text-red-500">{{ __('Failed to load customer') }}</p>
    <router-link to="/micro/customers" class="mt-2 inline-block text-sm text-gray-500 hover:text-gray-700">
      &larr; {{ __('Back to Customers') }}
    </router-link>
  </div>

  <div v-else-if="customer.data">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <router-link to="/micro/customers" class="text-sm text-gray-500 hover:text-gray-700">
          &larr; {{ __('Customers') }}
        </router-link>
        <h1 class="mt-1 text-2xl font-bold text-gray-900">
          {{ customer.data.customer.full_name }}
        </h1>
        <div class="mt-1 flex gap-2">
          <span
            class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
            :class="statusClasses[customer.data.customer.micro_status] || 'bg-gray-100 text-gray-600'"
          >
            {{ __(customer.data.customer.micro_status) }}
          </span>
          <span
            class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
            :class="customer.data.customer.micro_contact_type === 'Person' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
          >
            {{ __(customer.data.customer.micro_contact_type) }}
          </span>
          <span
            v-if="customer.data.customer.micro_source"
            class="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600"
          >
            {{ __(customer.data.customer.micro_source) }}
          </span>
        </div>
      </div>
      <a
        :href="`/app/contact/${props.id}`"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        {{ __('Edit in Desk') }}
      </a>
    </div>

    <!-- Capacity hint for potential customers -->
    <CapacityWidget v-if="customer.data.customer.micro_status === 'Potential'" :compact="true" class="mb-4" />

    <!-- Customer info grid -->
    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Contact Details') }}</h3>
        <dl class="space-y-2 text-sm">
          <div v-if="customer.data.customer.email_id">
            <dt class="text-gray-500">{{ __('Email') }}</dt>
            <dd class="text-gray-900">{{ customer.data.customer.email_id }}</dd>
          </div>
          <div v-if="customer.data.customer.phone">
            <dt class="text-gray-500">{{ __('Phone') }}</dt>
            <dd class="text-gray-900">{{ customer.data.customer.phone }}</dd>
          </div>
          <div v-if="customer.data.customer.mobile_no">
            <dt class="text-gray-500">{{ __('Mobile') }}</dt>
            <dd class="text-gray-900">{{ customer.data.customer.mobile_no }}</dd>
          </div>
          <div v-if="customer.data.customer.micro_website">
            <dt class="text-gray-500">{{ __('Website') }}</dt>
            <dd class="text-gray-900">{{ customer.data.customer.micro_website }}</dd>
          </div>
        </dl>
      </div>

      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Address') }}</h3>
        <dl class="space-y-2 text-sm">
          <div v-if="customer.data.customer.micro_address">
            <dd class="text-gray-900">{{ customer.data.customer.micro_address }}</dd>
          </div>
          <div v-if="customer.data.customer.micro_city || customer.data.customer.micro_postal_code">
            <dd class="text-gray-900">
              {{ [customer.data.customer.micro_postal_code, customer.data.customer.micro_city].filter(Boolean).join(' ') }}
            </dd>
          </div>
          <div v-if="customer.data.customer.micro_country">
            <dd class="text-gray-900">{{ customer.data.customer.micro_country }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Related notes -->
    <div v-if="customer.data.notes?.length" class="mb-6">
      <h3 class="mb-3 text-lg font-semibold text-gray-900">{{ __('Notes') }}</h3>
      <div class="space-y-2">
        <div
          v-for="note in customer.data.notes"
          :key="note.name"
          class="rounded-lg border border-gray-200 bg-white px-4 py-3"
        >
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-500">{{ __(note.note_type) }}</span>
            <span class="text-xs text-gray-400">{{ note.modified }}</span>
          </div>
          <p class="mt-1 text-sm text-gray-700">{{ note.content }}</p>
        </div>
      </div>
    </div>

  </div>
</template>
