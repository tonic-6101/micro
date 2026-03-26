<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { __ } from '@/composables/useTranslate'
import type { MicroCustomer } from '@/types/micro'

const props = defineProps<{
  customer: MicroCustomer
}>()

const router = useRouter()

function onDragStart(e: DragEvent) {
  e.dataTransfer?.setData('text/plain', props.customer.name)
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

function openCustomer() {
  router.push(`/micro/customers/${props.customer.name}`)
}
</script>

<template>
  <div
    draggable="true"
    class="cursor-grab rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow-md active:cursor-grabbing"
    @dragstart="onDragStart"
    @click="openCustomer"
  >
    <div class="flex items-start justify-between">
      <p class="text-sm font-medium text-gray-900">
        {{ customer.full_name }}
      </p>
      <span
        class="ml-2 inline-flex shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium"
        :class="customer.micro_contact_type === 'Person' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
      >
        {{ __(customer.micro_contact_type) }}
      </span>
    </div>

    <div class="mt-1.5 space-y-0.5">
      <p v-if="customer.email_id" class="truncate text-xs text-gray-500">
        {{ customer.email_id }}
      </p>
      <p v-if="customer.phone" class="text-xs text-gray-500">
        {{ customer.phone }}
      </p>
    </div>

    <div v-if="customer.micro_source" class="mt-2">
      <span class="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
        {{ __(customer.micro_source) }}
      </span>
    </div>
  </div>
</template>
