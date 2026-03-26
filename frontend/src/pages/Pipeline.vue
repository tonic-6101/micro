<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { PipelineResponse } from '@/types/micro'
import KanbanColumn from '@/components/pipeline/KanbanColumn.vue'

const showClosed = ref(false)

const pipeline = createResource({
  url: 'micro.api.pipeline.get_pipeline',
  params: { show_closed: showClosed.value },
  auto: true,
  transform(data: PipelineResponse) {
    return data
  },
})

const moveCustomer = createResource({
  url: 'micro.api.pipeline.move_customer',
})

function reloadPipeline() {
  pipeline.update({
    params: { show_closed: showClosed.value },
  })
  pipeline.reload()
}

function toggleClosed() {
  showClosed.value = !showClosed.value
  reloadPipeline()
}

function onDrop(customerId: string, stageId: string) {
  // Optimistic update: move the customer card locally
  if (pipeline.data) {
    let movedCustomer = null

    // Remove from current column
    for (const col of pipeline.data.stages) {
      const idx = col.customers.findIndex((c: { name: string }) => c.name === customerId)
      if (idx !== -1) {
        movedCustomer = col.customers.splice(idx, 1)[0]
        break
      }
    }

    // Check unassigned
    if (!movedCustomer) {
      const idx = pipeline.data.unassigned.findIndex((c: { name: string }) => c.name === customerId)
      if (idx !== -1) {
        movedCustomer = pipeline.data.unassigned.splice(idx, 1)[0]
      }
    }

    // Add to target column
    if (movedCustomer) {
      const targetCol = pipeline.data.stages.find(
        (col: { stage: { name: string } }) => col.stage.name === stageId,
      )
      if (targetCol) {
        movedCustomer.micro_pipeline_stage = stageId
        targetCol.customers.unshift(movedCustomer)
      }
    }
  }

  // Persist to server
  moveCustomer.submit({
    customer_id: customerId,
    stage_id: stageId,
  }).catch(() => {
    // On error, reload to get correct state
    reloadPipeline()
  })
}

const deskStagesUrl = computed(() => {
  return '/app/micro-pipeline-stage'
})
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Pipeline') }}
      </h1>
      <div class="flex items-center gap-3">
        <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            :checked="showClosed"
            class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
            @change="toggleClosed"
          />
          {{ __('Show closed stages') }}
        </label>
        <a
          :href="deskStagesUrl"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          {{ __('Edit Stages') }}
        </a>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="pipeline.loading && !pipeline.data" class="flex flex-1 items-center justify-center">
      <p class="text-sm text-gray-500">{{ __('Loading...') }}</p>
    </div>

    <!-- Error -->
    <div v-else-if="pipeline.error" class="flex flex-1 items-center justify-center">
      <p class="text-sm text-red-500">{{ __('Failed to load pipeline. Please try again.') }}</p>
    </div>

    <!-- Kanban Board -->
    <div v-else class="flex flex-1 gap-4 overflow-x-auto pb-4">
      <!-- Unassigned column (only if there are unassigned customers) -->
      <div
        v-if="pipeline.data?.unassigned?.length"
        class="flex w-72 shrink-0 flex-col rounded-lg border-t-4 border-gray-300 bg-gray-50"
      >
        <div class="flex items-center justify-between px-3 py-2.5">
          <h3 class="text-sm font-semibold text-gray-500">
            {{ __('Unassigned') }}
          </h3>
          <span class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-gray-100 px-1.5 text-[10px] font-medium text-gray-600">
            {{ pipeline.data.unassigned.length }}
          </span>
        </div>
        <div class="flex min-h-[100px] flex-1 flex-col gap-2 overflow-auto px-2 pb-2">
          <component
            :is="'div'"
            v-for="customer in pipeline.data.unassigned"
            :key="customer.name"
            draggable="true"
            class="cursor-grab rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow-md active:cursor-grabbing"
            @dragstart="(e: DragEvent) => { e.dataTransfer?.setData('text/plain', customer.name); if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move' }"
            @click="$router.push(`/micro/customers/${customer.name}`)"
          >
            <p class="text-sm font-medium text-gray-900">{{ customer.full_name }}</p>
            <p v-if="customer.email_id" class="mt-1 truncate text-xs text-gray-500">{{ customer.email_id }}</p>
          </component>
        </div>
      </div>

      <!-- Stage columns -->
      <KanbanColumn
        v-for="col in pipeline.data?.stages"
        :key="col.stage.name"
        :stage="col.stage"
        :customers="col.customers"
        @drop="onDrop"
      />

      <!-- Empty state -->
      <div
        v-if="!pipeline.data?.stages?.length"
        class="flex flex-1 flex-col items-center justify-center gap-2"
      >
        <p class="text-sm text-gray-500">{{ __('No pipeline stages configured') }}</p>
        <a
          :href="deskStagesUrl"
          class="text-sm font-medium text-gray-900 hover:text-gray-700"
        >
          {{ __('Edit Stages') }} &rarr;
        </a>
      </div>
    </div>
  </div>
</template>
