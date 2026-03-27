<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const props = defineProps<{ id: string }>()

const lead = createResource({
  url: 'micro.api.leads.get_lead',
  params: { lead_id: props.id },
  auto: true,
  transform(data: { lead: any }) {
    return data.lead
  },
})
</script>

<template>
  <div class="p-6">
    <router-link to="/micro/leads" class="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block">
      &larr; {{ __('Back to Leads') }}
    </router-link>

    <div v-if="lead.data" class="space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-semibold text-gray-900">{{ lead.data.lead_name }}</h1>
        <span
          class="rounded-full px-3 py-1 text-sm font-medium"
          :class="{
            'bg-green-100 text-green-800': lead.data.status === 'Won',
            'bg-red-100 text-red-800': lead.data.status === 'Lost',
            'bg-blue-100 text-blue-800': lead.data.status === 'Open',
            'bg-gray-100 text-gray-800': lead.data.status === 'Archived',
          }"
        >
          {{ lead.data.status }}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-4 rounded-lg border border-gray-200 p-4">
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Contact') }}</div>
          <div class="text-sm font-medium">{{ lead.data.contact || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Stage') }}</div>
          <div class="text-sm font-medium">{{ lead.data.stage || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Priority') }}</div>
          <div class="text-sm font-medium">{{ lead.data.priority || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Expected Value') }}</div>
          <div class="text-sm font-medium">{{ lead.data.expected_value || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Source') }}</div>
          <div class="text-sm font-medium">{{ lead.data.source || '\u2014' }}</div>
        </div>
        <div>
          <div class="text-xs text-gray-500 uppercase">{{ __('Next Follow-Up') }}</div>
          <div class="text-sm font-medium">{{ lead.data.next_follow_up || '\u2014' }}</div>
        </div>
      </div>

      <div v-if="lead.data.notes" class="rounded-lg border border-gray-200 p-4">
        <div class="text-xs text-gray-500 uppercase mb-2">{{ __('Notes') }}</div>
        <div class="text-sm text-gray-700" v-html="lead.data.notes"></div>
      </div>
    </div>

    <div v-else-if="lead.loading" class="text-center text-gray-500 py-8">
      {{ __('Loading...') }}
    </div>
  </div>
</template>
