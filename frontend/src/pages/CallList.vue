<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { CallListResponse, MicroLead, PipelinesListResponse } from '@/types/micro'

const route = useRoute()
const router = useRouter()

// Target group comes from the pipeline tabs, same as on the board.
const activePipeline = ref<string>((route.params.pipelineId as string) || '')
const includeUndated = ref(false)

const pipelines = createResource({
  url: 'micro.api.pipeline.get_pipelines',
  auto: true,
  transform(data: PipelinesListResponse) {
    return data
  },
  onSuccess(data: PipelinesListResponse) {
    if (!activePipeline.value) {
      activePipeline.value = data.default || data.pipelines[0]?.name || ''
    }
  },
})

const callList = createResource({
  url: 'micro.api.leads.get_call_list',
  transform(data: CallListResponse) {
    return data
  },
})

const snooze = createResource({ url: 'micro.api.leads.snooze_lead' })

const params = computed(() => ({
  pipeline: activePipeline.value || undefined,
  include_undated: includeUndated.value,
}))

const leads = computed<MicroLead[]>(() => callList.data?.leads || [])

const overdueCount = computed(() => leads.value.filter((lead) => lead.is_overdue).length)

function reload() {
  callList.update({ params: params.value })
  callList.reload()
}

watch(params, reload, { deep: true, immediate: true })

watch(activePipeline, (value) => {
  if (value && route.params.pipelineId !== value) {
    router.replace(`/micro/call-list/${value}`)
  }
})

function contactName(lead: MicroLead): string {
  const contact = lead.contact_details
  if (!contact) return ''
  const person = [contact.first_name, contact.last_name].filter(Boolean).join(' ').trim()
  return person || contact.company_name || ''
}

function phoneOf(lead: MicroLead): string {
  return lead.contact_details?.mobile_no || lead.contact_details?.phone || ''
}

function onSnooze(lead: MicroLead, days: number) {
  snooze.submit({ lead_id: lead.name, days }).then(reload)
}

function openLead(lead: MicroLead) {
  router.push(`/micro/leads/${lead.name}`)
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="mb-3 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ __('Call List') }}</h1>
        <p class="mt-0.5 text-xs text-gray-500">
          {{ leads.length }} {{ __('to work through') }}
          <span v-if="overdueCount"> &middot; {{ overdueCount }} {{ __('overdue') }}</span>
        </p>
      </div>
      <router-link
        :to="activePipeline ? `/micro/pipeline/${activePipeline}` : '/micro/pipeline'"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        {{ __('Pipeline') }}
      </router-link>
    </div>

    <!-- Pipeline tabs -->
    <div
      v-if="pipelines.data?.pipelines?.length"
      class="mb-3 flex items-center gap-1 overflow-x-auto border-b border-gray-200"
    >
      <button
        v-for="p in pipelines.data.pipelines"
        :key="p.name"
        type="button"
        class="shrink-0 border-b-2 px-3 py-2 text-sm font-medium transition"
        :class="
          p.name === activePipeline
            ? 'border-gray-900 text-gray-900'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        "
        @click="activePipeline = p.name"
      >
        {{ p.pipeline_name }}
      </button>
    </div>

    <!-- Filters -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-600">
        <input
          v-model="includeUndated"
          type="checkbox"
          class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
        />
        {{ __('Include leads without a follow-up date') }}
      </label>
    </div>

    <!-- Loading -->
    <div v-if="callList.loading && !callList.data" class="flex flex-1 items-center justify-center">
      <p class="text-sm text-gray-500">{{ __('Loading...') }}</p>
    </div>

    <!-- Empty -->
    <div v-else-if="!leads.length" class="flex flex-1 flex-col items-center justify-center gap-1">
      <p class="text-sm font-medium text-gray-700">{{ __('Nothing due today.') }}</p>
      <p class="text-xs text-gray-500">{{ __('Enjoy the quiet — or pick up the pipeline board.') }}</p>
    </div>

    <!-- Queue -->
    <div v-else class="flex-1 space-y-2 overflow-auto pb-4">
      <div
        v-for="lead in leads"
        :key="lead.name"
        class="rounded-lg border bg-white p-4 transition hover:shadow-sm"
        :class="lead.is_overdue ? 'border-red-200' : 'border-gray-200'"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <button
              type="button"
              class="text-left text-sm font-medium text-gray-900 hover:underline"
              @click="openLead(lead)"
            >
              {{ lead.lead_name }}
            </button>
            <p v-if="contactName(lead)" class="mt-0.5 text-xs text-gray-600">
              {{ contactName(lead) }}
              <span v-if="lead.stage_name"> &middot; {{ __(lead.stage_name) }}</span>
            </p>
            <p v-if="lead.contact_details?.micro_communication_style" class="mt-0.5 text-xs text-gray-500">
              {{ __(lead.contact_details.micro_communication_style) }}
            </p>
            <p v-if="lead.last_note?.subject" class="mt-1 truncate text-xs text-gray-500">
              {{ __('Last note') }}: {{ lead.last_note.subject }}
            </p>
          </div>

          <div class="flex items-center gap-2">
            <span
              v-if="lead.next_follow_up"
              class="rounded-full px-2 py-0.5 text-[11px] font-medium"
              :class="lead.is_overdue ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-600'"
            >
              {{ lead.next_follow_up }}
            </span>
            <a
              v-if="phoneOf(lead)"
              :href="`tel:${phoneOf(lead)}`"
              class="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-800"
            >
              {{ phoneOf(lead) }}
            </a>
            <span v-else class="text-xs text-gray-400">{{ __('No phone number') }}</span>
          </div>
        </div>

        <div class="mt-3 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-2">
          <button
            type="button"
            class="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
            @click="onSnooze(lead, 1)"
          >
            {{ __('Tomorrow') }}
          </button>
          <button
            type="button"
            class="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
            @click="onSnooze(lead, 7)"
          >
            {{ __('In a week') }}
          </button>
          <button
            type="button"
            class="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
            @click="onSnooze(lead, 30)"
          >
            {{ __('In a month') }}
          </button>
          <button
            type="button"
            class="ml-auto text-xs text-gray-500 underline hover:text-gray-900"
            @click="openLead(lead)"
          >
            {{ __('Open lead') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
