<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { OfferAcceptedMoment } from '@/types/micro'

const props = defineProps<{
  offerId: string
}>()

const emit = defineEmits<{
  dismiss: []
}>()

const show = ref(false)

const moment = createResource({
  url: 'micro.api.moments.get_offer_accepted_data',
  params: { offer_id: props.offerId },
  auto: true,
  transform(data: OfferAcceptedMoment) {
    // Trigger the entrance animation after data loads
    setTimeout(() => { show.value = true }, 100)
    return data
  },
})

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '\u2014'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}
</script>

<template>
  <Transition
    enter-active-class="transition duration-500 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
  >
    <div
      v-if="moment.data && show"
      class="relative overflow-hidden rounded-lg border border-green-200 bg-white"
    >
      <!-- Green accent bar -->
      <div class="h-1 bg-green-500" />

      <div class="p-5">
        <!-- Dismiss button -->
        <button
          class="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
          :aria-label="__('Dismiss')"
          @click="emit('dismiss')"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <!-- Headline -->
        <div class="mb-4 flex items-center gap-2">
          <span class="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 text-green-700">
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </span>
          <p class="text-sm font-medium text-gray-900">
            {{ moment.data.contact_name }} {{ __('accepted your offer.') }}
          </p>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs font-medium uppercase text-gray-500">{{ __('Project value') }}</p>
            <p class="mt-0.5 text-lg font-bold text-gray-900">
              {{ formatCurrency(moment.data.offer_total) }}
            </p>
          </div>
          <div>
            <p class="text-xs font-medium uppercase text-gray-500">{{ __('Pipeline this month') }}</p>
            <p class="mt-0.5 text-lg font-bold text-gray-900">
              {{ formatCurrency(moment.data.pipeline_this_month) }}
              <span
                v-if="moment.data.is_best_month"
                class="ml-1 inline-flex rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700"
              >
                {{ __('your best month to date') }}
              </span>
            </p>
          </div>
        </div>

        <!-- Follow-up hint + CTA -->
        <div class="mt-4 flex items-center justify-between border-t border-gray-100 pt-4">
          <p class="text-xs text-gray-500">
            {{ __("We'll remind you to follow up on next steps in 3 days.") }}
          </p>
          <a
            :href="`/app/micro-invoice-draft/new?offer_draft=${offerId}`"
            class="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
          >
            {{ __('Create Invoice Draft') }}
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  </Transition>
</template>
