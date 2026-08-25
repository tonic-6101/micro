<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { __ } from '@/composables/useTranslate'
import FieldLabel from '@/components/FieldLabel.vue'
import type { MicroLead } from '@/types/micro'

const props = defineProps<{
  lead: MicroLead
}>()

const router = useRouter()

// An import names the lead after the contact, so this line would echo the title
// on nearly every card. Show whichever of the two the title does not already
// say — the person's employer, say — and otherwise nothing at all.
const contactLabel = computed(() => {
  const contact = props.lead.contact_details
  if (!contact) return ''

  const title = (props.lead.lead_name || '').trim()
  const person = [contact.first_name, contact.last_name].filter(Boolean).join(' ').trim()
  const company = (contact.company_name || '').trim()

  return [person, company].find((label) => label && label !== title) || ''
})

/** The contact's tags, as chips. Frappe stores them comma-joined. */
const tags = computed(() =>
  (props.lead.contact_details?._user_tags || '').split(',').filter(Boolean),
)

const phone = computed(() => {
  const contact = props.lead.contact_details
  return contact?.mobile_no || contact?.phone || ''
})

// Straight-line kilometres, worked out server-side. `0` is a real answer — the
// contact shares your postal code — so only `null`/absent means "unknown".
const distance = computed(() => {
  const km = props.lead.contact_details?.distance_km
  return typeof km === 'number' ? km : null
})

const isOverdue = computed(() => {
  if (!props.lead.next_follow_up) return false
  return props.lead.next_follow_up <= new Date().toISOString().slice(0, 10)
})

const priorityClass = computed(() => {
  switch (props.lead.priority) {
    case 'High':
      return 'bg-red-100 text-red-800'
    case 'Low':
      return 'bg-gray-100 text-gray-600'
    default:
      return 'bg-blue-100 text-blue-800'
  }
})

function onDragStart(e: DragEvent) {
  e.dataTransfer?.setData('text/plain', props.lead.name)
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
  }
}

function openLead() {
  router.push(`/micro/leads/${props.lead.name}`)
}

function openContact(e: Event) {
  e.stopPropagation()
  if (props.lead.contact) {
    router.push(`/micro/customers/${props.lead.contact}`)
  }
}
</script>

<template>
  <div
    draggable="true"
    class="min-w-0 cursor-grab rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow-md active:cursor-grabbing"
    @dragstart="onDragStart"
    @click="openLead"
  >
    <div class="flex items-start justify-between gap-2">
      <!-- Imported names run long. Two lines keep the cards scannable; the rest
           is one hover away, and the card opens the lead anyway. -->
      <p
        class="line-clamp-2 min-w-0 break-words text-sm font-medium text-gray-900"
        :title="lead.lead_name"
      >
        {{ lead.lead_name }}
      </p>
      <span
        v-if="lead.priority && lead.priority !== 'Medium'"
        class="inline-flex shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium"
        :class="priorityClass"
      >
        {{ __(lead.priority) }}
      </span>
    </div>

    <!-- `block w-full`, or the button sizes to its text and `truncate` never bites. -->
    <button
      v-if="contactLabel"
      type="button"
      class="mt-1 block w-full truncate text-left text-xs text-gray-600 hover:text-gray-900 hover:underline"
      :title="contactLabel"
      @click="openContact"
    >
      {{ contactLabel }}
    </button>

    <p v-if="phone" class="mt-0.5 truncate text-xs text-gray-500" :title="phone">
      {{ phone }}
    </p>

    <!-- How far the job is. Straight-line, so the label says so on hover
         rather than letting the number pass for a drive. -->
    <FieldLabel
      v-if="distance !== null"
      field="distance_km"
      :uppercase="false"
      class="mt-0.5 !font-normal"
    >
      {{ distance }} {{ __('km') }}
    </FieldLabel>

    <!-- Tags are the contact's own words about a lead — square chips, so they
         read apart from the round metadata pills below. -->
    <div v-if="tags.length" class="mt-1.5 flex flex-wrap items-center gap-1">
      <span
        v-for="tag in tags.slice(0, 3)"
        :key="tag"
        class="inline-flex max-w-full truncate rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600"
        :title="tag"
      >
        {{ tag }}
      </span>
      <span
        v-if="tags.length > 3"
        class="text-[10px] text-gray-400"
        :title="tags.slice(3).join(', ')"
      >
        +{{ tags.length - 3 }}
      </span>
    </div>

    <div class="mt-2 flex flex-wrap items-center gap-1.5">
      <span
        v-if="lead.expected_value"
        class="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-700"
      >
        {{ lead.expected_value.toLocaleString('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }) }}
      </span>
      <span
        v-if="lead.source"
        class="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600"
      >
        {{ __(lead.source) }}
      </span>
      <span
        v-if="lead.next_follow_up"
        class="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium"
        :class="isOverdue ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-600'"
      >
        {{ isOverdue ? __('Due') : __('Follow-up') }}: {{ lead.next_follow_up }}
      </span>
    </div>
  </div>
</template>
