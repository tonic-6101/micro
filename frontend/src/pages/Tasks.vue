<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 20

const tasks = createResource({
  url: 'micro.api.tasks.get_tasks',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { tasks: any[]; total: number }) {
    return data
  },
})

watch([search, statusFilter, page], () => {
  const filters: Record<string, any> = {}
  if (statusFilter.value) filters.status = statusFilter.value

  tasks.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      search: search.value,
      filters: Object.keys(filters).length ? filters : undefined,
    },
  })
  tasks.reload()
})
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold text-gray-900">{{ __('Tasks') }}</h1>
    </div>

    <div class="flex gap-3 mb-4">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search tasks...')"
        class="w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm"
      />
      <select
        v-model="statusFilter"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm"
      >
        <option value="">{{ __('All statuses') }}</option>
        <option value="Open">{{ __('Open') }}</option>
        <option value="In Progress">{{ __('In Progress') }}</option>
        <option value="Completed">{{ __('Completed') }}</option>
        <option value="Cancelled">{{ __('Cancelled') }}</option>
      </select>
    </div>

    <div v-if="tasks.data?.tasks?.length" class="space-y-2">
      <router-link
        v-for="task in tasks.data.tasks"
        :key="task.name"
        :to="`/micro/tasks/${task.name}`"
        class="block rounded-lg border border-gray-200 p-4 hover:bg-gray-50"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span
              class="inline-block h-2 w-2 rounded-full"
              :class="{
                'bg-green-500': task.status === 'Completed',
                'bg-blue-500': task.status === 'In Progress',
                'bg-gray-400': task.status === 'Open',
                'bg-red-400': task.status === 'Cancelled',
              }"
            ></span>
            <span class="font-medium text-gray-900">{{ task.subject }}</span>
          </div>
          <div class="flex items-center gap-2 text-xs text-gray-500">
            <span v-if="task.due_date">{{ task.due_date }}</span>
            <span
              class="rounded-full px-2 py-0.5"
              :class="{
                'bg-red-50 text-red-700': task.priority === 'High',
                'bg-yellow-50 text-yellow-700': task.priority === 'Medium',
                'bg-gray-50 text-gray-600': task.priority === 'Low',
              }"
            >
              {{ task.priority }}
            </span>
          </div>
        </div>
      </router-link>
    </div>

    <div v-else-if="tasks.loading" class="text-center text-gray-500 py-8">
      {{ __('Loading...') }}
    </div>

    <div v-else class="text-center text-gray-500 py-8">
      {{ __('No tasks yet') }}
    </div>
  </div>
</template>
