<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<template>
  <!-- Compact mode: inline hint banner -->
  <div v-if="compact && capacity.data" :class="compactClasses" class="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm">
    <span>{{ compactMessage }}</span>
  </div>

  <!-- Full mode: dashboard card -->
  <div v-else-if="!compact && capacity.data" class="rounded-lg border border-gray-200 bg-white p-5">
    <div class="mb-3 flex items-baseline justify-between">
      <h3 class="text-sm font-medium text-gray-500">
        {{ __('Capacity') }} — {{ capacity.data.month_label }}
      </h3>
      <span v-if="capacity.data.source === 'orga_estimate'" class="text-xs text-amber-600">
        {{ __('Based on task estimates, not logged time') }}
      </span>
    </div>

    <!-- No data state -->
    <div v-if="capacity.data.source === 'none'" class="py-4 text-center">
      <p class="text-sm text-gray-500">
        {{ __('Log time in Watch to see your capacity') }}
      </p>
      <p class="mt-1 text-xs text-gray-400">
        {{ __('Or add estimated hours to your Orga tasks') }}
      </p>
    </div>

    <!-- Capacity display -->
    <div v-else>
      <div class="mb-2 h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="barColor"
          :style="{ width: capacity.data.percentage + '%' }"
        />
      </div>

      <div class="mb-2 flex items-baseline justify-between">
        <span class="text-2xl font-bold text-gray-900">{{ capacity.data.percentage }}%</span>
        <span class="text-xs text-gray-400">
          ~{{ capacity.data.available_hours }}{{ __('h available') }}
        </span>
      </div>

      <p class="text-sm" :class="statusTextColor">
        {{ capacity.data.status_message }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { CapacityData } from '@/types/micro'

const props = withDefaults(defineProps<{ compact?: boolean }>(), {
  compact: false,
})

const capacity = createResource({
  url: 'micro.api.capacity.get_capacity_data',
  auto: true,
  transform: (data: CapacityData) => data,
})

const barColor = computed(() => {
  const colors: Record<string, string> = {
    low: 'bg-blue-400',
    good: 'bg-green-500',
    nearly_full: 'bg-amber-400',
    overcommitted: 'bg-red-500',
  }
  return colors[capacity.data?.status_key ?? 'low']
})

const statusTextColor = computed(() => {
  const colors: Record<string, string> = {
    low: 'text-blue-600',
    good: 'text-green-600',
    nearly_full: 'text-amber-600',
    overcommitted: 'text-red-600',
  }
  return colors[capacity.data?.status_key ?? 'low']
})

const compactClasses = computed(() => {
  const styles: Record<string, string> = {
    low: 'border-blue-200 bg-blue-50 text-blue-700',
    good: 'border-green-200 bg-green-50 text-green-700',
    nearly_full: 'border-amber-200 bg-amber-50 text-amber-700',
    overcommitted: 'border-red-200 bg-red-50 text-red-700',
  }
  return styles[capacity.data?.status_key ?? 'low']
})

const compactMessage = computed(() => {
  if (!capacity.data || capacity.data.source === 'none') {
    return __('Log time in Watch to see your capacity')
  }
  if (capacity.data.raw_percentage > 95) {
    return __("You're at {pct}% capacity this month. Consider a later start date or adjusting your rate.", {
      pct: String(capacity.data.percentage),
    })
  }
  return __('~{hours}h available this month', {
    hours: String(capacity.data.available_hours),
  })
})
</script>
