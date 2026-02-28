<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { createListResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const tasks = createListResource({
  doctype: 'Micro Task',
  fields: ['name', 'title', 'status', 'priority', 'due_date', 'contact'],
  orderBy: 'due_date asc',
  pageLength: 50,
  auto: true,
})
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Tasks') }}
      </h1>
      <a
        href="/app/micro-task/new"
        class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
      >
        {{ __('New Task') }}
      </a>
    </div>

    <div v-if="tasks.list.loading" class="py-8 text-center text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Task') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Status') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Priority') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Due Date') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="task in tasks.data"
            :key="task.name"
            class="hover:bg-gray-50"
          >
            <td class="px-4 py-3 text-sm font-medium text-gray-900">
              {{ task.title }}
            </td>
            <td class="px-4 py-3 text-sm">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="{
                  'bg-green-100 text-green-800': task.status === 'Completed',
                  'bg-yellow-100 text-yellow-800': task.status === 'Open',
                  'bg-blue-100 text-blue-800': task.status === 'In Progress',
                  'bg-gray-100 text-gray-800': task.status === 'Cancelled',
                }"
              >
                {{ __(task.status) }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-500">
              {{ task.priority || '—' }}
            </td>
            <td class="px-4 py-3 text-sm text-gray-500">
              {{ task.due_date || '—' }}
            </td>
          </tr>

          <tr v-if="!tasks.data?.length">
            <td colspan="4" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ __('No tasks yet') }}</p>
              <a
                href="/app/micro-task/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Create your first task') }} &rarr;
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
