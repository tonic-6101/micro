<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const search = ref('')
const page = ref(1)
const pageSize = 20

const leads = createResource({
  url: 'micro.api.leads.get_leads',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { leads: any[]; total: number }) {
    return data
  },
})

watch([search, page], () => {
  leads.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      search: search.value,
    },
  })
  leads.reload()
})
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-semibold text-gray-900">{{ __('Leads') }}</h1>
      <div class="flex items-center gap-4">
        <router-link
          to="/micro/leads/trash"
          class="text-sm text-gray-500 hover:text-gray-700"
        >
          {{ __('Trash') }}
        </router-link>
        <router-link
          to="/micro/pipeline"
          class="text-sm text-blue-600 hover:text-blue-800"
        >
          {{ __('Pipeline View') }}
        </router-link>
      </div>
    </div>

    <div class="mb-4">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search leads...')"
        class="w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm"
      />
    </div>

    <div v-if="leads.data?.leads?.length" class="space-y-2">
      <router-link
        v-for="lead in leads.data.leads"
        :key="lead.name"
        :to="`/micro/leads/${lead.name}`"
        class="block rounded-lg border border-gray-200 p-4 hover:bg-gray-50"
      >
        <div class="flex items-center justify-between">
          <div>
            <span class="font-medium text-gray-900">{{ lead.lead_name }}</span>
            <span v-if="lead.contact" class="ml-2 text-sm text-gray-500">{{ lead.contact }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="rounded-full px-2 py-0.5 text-xs font-medium"
              :class="{
                'bg-green-100 text-green-800': lead.status === 'Won',
                'bg-red-100 text-red-800': lead.status === 'Lost',
                'bg-blue-100 text-blue-800': lead.status === 'Open',
                'bg-gray-100 text-gray-800': lead.status === 'Archived',
              }"
            >
              {{ lead.status }}
            </span>
            <span
              class="rounded-full px-2 py-0.5 text-xs"
              :class="{
                'bg-red-50 text-red-700': lead.priority === 'High',
                'bg-yellow-50 text-yellow-700': lead.priority === 'Medium',
                'bg-gray-50 text-gray-600': lead.priority === 'Low',
              }"
            >
              {{ lead.priority }}
            </span>
          </div>
        </div>
        <div v-if="lead.next_follow_up" class="mt-1 text-xs text-gray-500">
          {{ __('Follow-up') }}: {{ lead.next_follow_up }}
        </div>
      </router-link>
    </div>

    <div v-else-if="leads.loading" class="text-center text-gray-500 py-8">
      {{ __('Loading...') }}
    </div>

    <div v-else class="text-center text-gray-500 py-8">
      {{ __('No leads yet') }}
    </div>
  </div>
</template>
