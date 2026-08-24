<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { MicroPipelineStage, MicroLead } from '@/types/micro'
import KanbanCard from './KanbanCard.vue'

const props = defineProps<{
  stage: MicroPipelineStage
  leads: MicroLead[]
  /** Total in this column, which can be far more than the page shown. */
  count?: number
  value?: number
}>()

const total = computed(() => props.count ?? props.leads.length)
const isTruncated = computed(() => total.value > props.leads.length)

const emit = defineEmits<{
  drop: [leadId: string, stageId: string]
  add: [stageId: string]
}>()

const isDragOver = ref(false)

const colorMap: Record<string, string> = {
  Gray: 'border-gray-400',
  Blue: 'border-blue-500',
  Green: 'border-green-500',
  Yellow: 'border-yellow-500',
  Orange: 'border-orange-500',
  Red: 'border-red-500',
  Purple: 'border-purple-500',
  Pink: 'border-pink-500',
}

const bgColorMap: Record<string, string> = {
  Gray: 'bg-gray-50',
  Blue: 'bg-blue-50',
  Green: 'bg-green-50',
  Yellow: 'bg-yellow-50',
  Orange: 'bg-orange-50',
  Red: 'bg-red-50',
  Purple: 'bg-purple-50',
  Pink: 'bg-pink-50',
}

const formattedValue = computed(() => {
  if (!props.value) return ''
  return props.value.toLocaleString('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  })
})

function onDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
  const leadId = e.dataTransfer?.getData('text/plain')
  if (leadId) {
    emit('drop', leadId, props.stage.name)
  }
}
</script>

<template>
  <div
    class="flex w-72 shrink-0 flex-col rounded-lg border-t-4 bg-gray-50"
    :class="[
      colorMap[stage.color || 'Gray'],
      isDragOver ? 'ring-2 ring-gray-400 ring-offset-1' : '',
    ]"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <!-- Column header -->
    <div class="px-3 py-2.5">
      <div class="flex items-center justify-between gap-2">
        <h3 class="min-w-0 truncate text-sm font-semibold text-gray-700" :title="__(stage.stage_name)">
          {{ __(stage.stage_name) }}
        </h3>
        <div class="flex shrink-0 items-center gap-1.5">
          <span
            class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[10px] font-medium text-gray-600"
            :class="bgColorMap[stage.color || 'Gray']"
          >
            {{ total }}
          </span>
          <button
            type="button"
            class="text-base leading-none text-gray-400 hover:text-gray-900"
            :title="__('New lead in this stage')"
            @click="emit('add', stage.name)"
          >
            +
          </button>
        </div>
      </div>
      <p v-if="formattedValue" class="mt-0.5 text-[11px] text-gray-500">
        {{ formattedValue }}
      </p>
      <p v-if="isTruncated" class="mt-0.5 text-[11px] text-gray-400">
        {{ __('Showing') }} {{ leads.length }} {{ __('of') }} {{ total }}
      </p>
    </div>

    <!-- Cards -->
    <div
      class="flex min-h-[100px] flex-1 flex-col gap-2 overflow-y-auto overflow-x-hidden px-2 pb-2"
      :class="isDragOver ? 'bg-gray-100/50' : ''"
    >
      <KanbanCard v-for="lead in leads" :key="lead.name" :lead="lead" />
      <p v-if="!leads.length" class="py-8 text-center text-xs text-gray-400">
        {{ __('No leads') }}
      </p>
    </div>
  </div>
</template>
