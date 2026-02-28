<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref } from 'vue'
import { __ } from '@/composables/useTranslate'
import type { MicroPipelineStage, MicroCustomer } from '@/types/micro'
import KanbanCard from './KanbanCard.vue'

const props = defineProps<{
  stage: MicroPipelineStage
  customers: MicroCustomer[]
}>()

const emit = defineEmits<{
  drop: [customerId: string, stageId: string]
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
  const customerId = e.dataTransfer?.getData('text/plain')
  if (customerId) {
    emit('drop', customerId, props.stage.name)
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
    <div class="flex items-center justify-between px-3 py-2.5">
      <h3 class="text-sm font-semibold text-gray-700">
        {{ __(stage.stage_name) }}
      </h3>
      <span
        class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[10px] font-medium"
        :class="bgColorMap[stage.color || 'Gray'] + ' text-gray-600'"
      >
        {{ customers.length }}
      </span>
    </div>

    <!-- Cards -->
    <div
      class="flex min-h-[100px] flex-1 flex-col gap-2 overflow-auto px-2 pb-2"
      :class="isDragOver ? 'bg-gray-100/50' : ''"
    >
      <KanbanCard
        v-for="customer in customers"
        :key="customer.name"
        :customer="customer"
      />
      <p
        v-if="!customers.length"
        class="py-8 text-center text-xs text-gray-400"
      >
        {{ __('No customers') }}
      </p>
    </div>
  </div>
</template>
