<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const props = defineProps<{ id: string }>()

const task = createResource({
  url: 'micro.api.tasks.get_task',
  params: { task_id: props.id },
  auto: true,
  transform(data: { task: any }) {
    return data.task
  },
})
</script>

<template>
  <div class="p-6">
    <router-link to="/micro/tasks" class="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block">
      &larr; {{ __('Back to Tasks') }}
    </router-link>

    <div v-if="task.data" class="space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-semibold text-gray-900">{{ task.data.subject }}</h1>
        <span
          class="rounded-full px-3 py-1 text-sm font-medium"
          :class="{
            'bg-green-100 text-green-800': task.data.status === 'Completed',
            'bg-blue-100 text-blue-800': task.data.status === 'In Progress',
            'bg-gray-100 text-gray-800': task.data.status === 'Open',
            'bg-red-100 text-red-800': task.data.status === 'Cancelled',
          }"
        >
          {{ task.data.status }}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-4 rounded-lg border border-gray-200 p-4">
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Priority') }}</div>
          <div class="text-sm font-medium">{{ task.data.priority || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Due Date') }}</div>
          <div class="text-sm font-medium">{{ task.data.due_date || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Contact') }}</div>
          <div class="text-sm font-medium">{{ task.data.contact || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Lead') }}</div>
          <div class="text-sm font-medium">{{ task.data.lead || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Assigned To') }}</div>
          <div class="text-sm font-medium">{{ task.data.assigned_to || '\u2014' }}</div>
        </div>
      </div>

      <div v-if="task.data.description" class="rounded-lg border border-gray-200 p-4">
        <div class="text-xs text-gray-500 uppercase mb-2">{{ __('Description') }}</div>
        <div class="text-sm text-gray-700" v-html="task.data.description"></div>
      </div>
    </div>

    <div v-else-if="task.loading" class="text-center text-gray-500 py-8">
      {{ __('Loading...') }}
    </div>
  </div>
</template>
