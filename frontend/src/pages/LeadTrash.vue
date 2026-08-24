<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { TrashedLeadsResponse, MicroLead } from '@/types/micro'

const search = ref('')
const confirmingDelete = ref('')
const actionError = ref('')
let debounce: ReturnType<typeof setTimeout> | undefined

const trash = createResource({
  url: 'micro.api.leads.get_archived_leads',
  params: { limit_page_length: 50 },
  auto: true,
  transform(data: TrashedLeadsResponse) {
    return data
  },
})

const restoreLead = createResource({ url: 'micro.api.leads.restore_lead' })
const deleteLead = createResource({ url: 'micro.api.leads.delete_lead' })

const leads = computed<MicroLead[]>(() => trash.data?.leads || [])
const canDelete = computed(() => Boolean(trash.data?.can_delete))

watch(search, (value) => {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    trash.update({ params: { search: value.trim() || undefined, limit_page_length: 50 } })
    trash.reload()
  }, 250)
})

function contactName(lead: MicroLead): string {
  const details = lead.contact_details
  if (!details) return ''
  return details.full_name || details.company_name || details.name
}

function reload() {
  confirmingDelete.value = ''
  trash.reload()
}

function onError(err: unknown, fallback: string) {
  actionError.value = (err as { messages?: string[] })?.messages?.[0] || fallback
}

function onRestore(leadId: string) {
  actionError.value = ''
  restoreLead
    .submit({ lead_id: leadId })
    .then(reload)
    .catch((err: unknown) => onError(err, __('Failed to restore lead')))
}

function onDelete(leadId: string) {
  actionError.value = ''
  deleteLead
    .submit({ lead_id: leadId })
    .then(reload)
    .catch((err: unknown) => onError(err, __('Failed to delete lead')))
}
</script>

<template>
  <div class="p-6">
    <router-link
      to="/micro/leads"
      class="mb-4 inline-block text-sm text-gray-500 hover:text-gray-700"
    >
      &larr; {{ __('Back to Leads') }}
    </router-link>

    <div class="mb-2 flex items-center justify-between">
      <h1 class="text-xl font-semibold text-gray-900">{{ __('Trash') }}</h1>
      <span v-if="trash.data" class="text-xs text-gray-500">
        {{ trash.data.total }} {{ __('leads in the trash') }}
      </span>
    </div>
    <p class="mb-4 text-xs text-gray-500">
      {{ __('Leads in the trash are off every board and list. Restore one to put it back where it was.') }}
    </p>

    <input
      v-model="search"
      type="text"
      :placeholder="__('Search trash...')"
      class="mb-4 w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
    />

    <p v-if="actionError" class="mb-3 text-sm text-red-600">{{ actionError }}</p>

    <div v-if="trash.loading && !trash.data" class="py-8 text-center text-sm text-gray-500">
      {{ __('Loading...') }}
    </div>

    <div v-else-if="!leads.length" class="py-12 text-center">
      <p class="text-sm text-gray-500">{{ __('The trash is empty') }}</p>
    </div>

    <ul v-else class="divide-y divide-gray-100 rounded-lg border border-gray-200">
      <li
        v-for="lead in leads"
        :key="lead.name"
        class="flex flex-wrap items-center justify-between gap-3 px-4 py-3"
      >
        <div class="min-w-0">
          <router-link
            :to="`/micro/leads/${lead.name}`"
            class="text-sm font-medium text-gray-900 hover:underline"
          >
            {{ lead.lead_name }}
          </router-link>
          <p class="truncate text-xs text-gray-500">
            <span v-if="contactName(lead)">{{ contactName(lead) }} &middot; </span>
            <span v-if="lead.stage_name">{{ __(lead.stage_name) }} &middot; </span>
            {{ lead.pipeline }}
          </p>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <!-- Confirm inline, the way the pipeline dialog does -->
          <template v-if="confirmingDelete === lead.name">
            <span class="text-xs text-gray-600">{{ __('Delete for good?') }}</span>
            <button
              type="button"
              class="rounded bg-red-600 px-2 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="deleteLead.loading"
              @click="onDelete(lead.name)"
            >
              {{ __('Yes, delete permanently') }}
            </button>
            <button
              type="button"
              class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
              @click="confirmingDelete = ''"
            >
              {{ __('Cancel') }}
            </button>
          </template>

          <template v-else>
            <button
              type="button"
              class="rounded border border-gray-300 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              :disabled="restoreLead.loading"
              @click="onRestore(lead.name)"
            >
              {{ __('Restore') }}
            </button>
            <button
              v-if="canDelete"
              type="button"
              class="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
              @click="confirmingDelete = lead.name"
            >
              {{ __('Delete') }}
            </button>
          </template>
        </div>
      </li>
    </ul>
  </div>
</template>
