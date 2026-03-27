<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CapacityWidget from '@/components/CapacityWidget.vue'
import type { CustomerDetailResponse, MicroCustomer } from '@/types/micro'

const props = defineProps<{
  id: string
}>()

const customer = createResource({
  url: 'micro.api.customers.get_customer',
  params: { customer_id: props.id },
  auto: true,
  transform(data: CustomerDetailResponse) {
    return data
  },
})

const statusClasses: Record<string, string> = {
  Potential: 'bg-blue-100 text-blue-800',
  Active: 'bg-green-100 text-green-800',
  Inactive: 'bg-gray-100 text-gray-600',
}

const gradeClasses: Record<string, string> = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-blue-100 text-blue-800',
  C: 'bg-amber-100 text-amber-800',
  D: 'bg-red-100 text-red-800',
}

const c = computed(() => customer.data?.customer as MicroCustomer | undefined)

// Intelligence Card inline editing
const editingField = ref<string | null>(null)
const editValue = ref('')
const lastContactTopic = ref('')

const communicationStyles = [
  '', 'Email-first', 'Phone-first', 'WhatsApp',
  'Async (slow replies OK)', 'Needs quick responses',
]

const updateIntelligence = createResource({
  url: 'micro.api.customers.update_intelligence',
  onSuccess() {
    editingField.value = null
    customer.reload()
  },
})

function startEdit(field: string, currentValue: string | undefined) {
  editingField.value = field
  editValue.value = currentValue || ''
}

function startEditLastContact() {
  editingField.value = 'micro_last_contact'
  editValue.value = c.value?.micro_last_contact_date || ''
  lastContactTopic.value = c.value?.micro_last_contact_topic || ''
}

function saveField(field: string) {
  updateIntelligence.submit({ customer_id: props.id, [field]: editValue.value })
}

function saveLastContact() {
  updateIntelligence.submit({
    customer_id: props.id,
    micro_last_contact_date: editValue.value,
    micro_last_contact_topic: lastContactTopic.value,
  })
}

function cancelEdit() {
  editingField.value = null
  editValue.value = ''
}
</script>

<template>
  <div v-if="customer.loading" class="py-12 text-center text-sm text-gray-500">
    {{ __('Loading...') }}
  </div>

  <div v-else-if="customer.error" class="py-12 text-center">
    <p class="text-sm text-red-500">{{ __('Failed to load customer') }}</p>
    <router-link to="/micro/customers" class="mt-2 inline-block text-sm text-gray-500 hover:text-gray-700">
      &larr; {{ __('Back to Customers') }}
    </router-link>
  </div>

  <div v-else-if="customer.data && c">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <div>
        <router-link to="/micro/customers" class="text-sm text-gray-500 hover:text-gray-700">
          &larr; {{ __('Customers') }}
        </router-link>
        <h1 class="mt-1 text-2xl font-bold text-gray-900">
          {{ c.full_name }}
        </h1>
        <div class="mt-1 flex gap-2">
          <span
            class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
            :class="statusClasses[c.micro_status] || 'bg-gray-100 text-gray-600'"
          >
            {{ __(c.micro_status) }}
          </span>
          <span
            class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
            :class="c.micro_contact_type === 'Person' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
          >
            {{ __(c.micro_contact_type) }}
          </span>
          <span
            v-if="c.micro_source"
            class="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600"
          >
            {{ __(c.micro_source) }}
          </span>
          <span
            v-if="c.micro_health_score"
            class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold"
            :class="gradeClasses[c.micro_health_score] || 'bg-gray-100 text-gray-500'"
          >
            {{ c.micro_health_score }}
          </span>
        </div>
      </div>
      <a
        :href="`/app/contact/${props.id}`"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        {{ __('Edit in Desk') }}
      </a>
    </div>

    <!-- Capacity hint for potential customers -->
    <CapacityWidget v-if="c.micro_status === 'Potential'" :compact="true" class="mb-4" />

    <!-- Client Intelligence Card — second panel, always visible -->
    <div class="mb-6 rounded-lg border border-gray-200 bg-white p-4">
      <h3 class="mb-4 text-lg font-semibold text-gray-900">{{ __('Client Intelligence') }}</h3>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <!-- What they love -->
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('What they love') }}</label>
          <div v-if="editingField === 'micro_client_loves'">
            <textarea
              v-model="editValue"
              rows="3"
              maxlength="500"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              @keydown.escape="cancelEdit"
            />
            <div class="mt-1 flex gap-1">
              <button class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700" @click="saveField('micro_client_loves')">{{ __('Save') }}</button>
              <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200" @click="cancelEdit">{{ __('Cancel') }}</button>
            </div>
          </div>
          <p
            v-else
            class="cursor-pointer whitespace-pre-wrap rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            :class="{ 'italic text-gray-400': !c.micro_client_loves }"
            @click="startEdit('micro_client_loves', c.micro_client_loves)"
          >
            {{ c.micro_client_loves || __('Click to add...') }}
          </p>
        </div>

        <!-- What to avoid -->
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('What to avoid') }}</label>
          <div v-if="editingField === 'micro_client_avoid'">
            <textarea
              v-model="editValue"
              rows="3"
              maxlength="500"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              @keydown.escape="cancelEdit"
            />
            <div class="mt-1 flex gap-1">
              <button class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700" @click="saveField('micro_client_avoid')">{{ __('Save') }}</button>
              <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200" @click="cancelEdit">{{ __('Cancel') }}</button>
            </div>
          </div>
          <p
            v-else
            class="cursor-pointer whitespace-pre-wrap rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            :class="{ 'italic text-gray-400': !c.micro_client_avoid }"
            @click="startEdit('micro_client_avoid', c.micro_client_avoid)"
          >
            {{ c.micro_client_avoid || __('Click to add...') }}
          </p>
        </div>

        <!-- Communication style -->
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Communication style') }}</label>
          <div v-if="editingField === 'micro_communication_style'">
            <select
              v-model="editValue"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option v-for="opt in communicationStyles" :key="opt" :value="opt">
                {{ opt || __('Not set') }}
              </option>
            </select>
            <div class="mt-1 flex gap-1">
              <button class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700" @click="saveField('micro_communication_style')">{{ __('Save') }}</button>
              <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200" @click="cancelEdit">{{ __('Cancel') }}</button>
            </div>
          </div>
          <p
            v-else
            class="cursor-pointer rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            :class="{ 'italic text-gray-400': !c.micro_communication_style }"
            @click="startEdit('micro_communication_style', c.micro_communication_style)"
          >
            {{ c.micro_communication_style ? __(c.micro_communication_style) : __('Click to set...') }}
          </p>
        </div>

        <!-- Personal notes -->
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Personal notes') }}</label>
          <div v-if="editingField === 'micro_personal_notes'">
            <textarea
              v-model="editValue"
              rows="3"
              maxlength="500"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              @keydown.escape="cancelEdit"
            />
            <div class="mt-1 flex gap-1">
              <button class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700" @click="saveField('micro_personal_notes')">{{ __('Save') }}</button>
              <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200" @click="cancelEdit">{{ __('Cancel') }}</button>
            </div>
          </div>
          <p
            v-else
            class="cursor-pointer whitespace-pre-wrap rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            :class="{ 'italic text-gray-400': !c.micro_personal_notes }"
            @click="startEdit('micro_personal_notes', c.micro_personal_notes)"
          >
            {{ c.micro_personal_notes || __('Click to add...') }}
          </p>
        </div>

        <!-- Opportunities spotted -->
        <div class="sm:col-span-2">
          <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Opportunities spotted') }}</label>
          <div v-if="editingField === 'micro_opportunities'">
            <textarea
              v-model="editValue"
              rows="3"
              maxlength="500"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              @keydown.escape="cancelEdit"
            />
            <div class="mt-1 flex gap-1">
              <button class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700" @click="saveField('micro_opportunities')">{{ __('Save') }}</button>
              <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200" @click="cancelEdit">{{ __('Cancel') }}</button>
            </div>
          </div>
          <div v-else>
            <p
              class="cursor-pointer whitespace-pre-wrap rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              :class="{ 'italic text-gray-400': !c.micro_opportunities }"
              @click="startEdit('micro_opportunities', c.micro_opportunities)"
            >
              {{ c.micro_opportunities || __('Click to add...') }}
            </p>
            <router-link
              v-if="c.micro_opportunities"
              :to="`/micro/offers/new?contact=${props.id}`"
              class="mt-1 inline-block text-xs font-medium text-blue-600 hover:text-blue-700"
            >
              + {{ __('Create offer draft') }}
            </router-link>
          </div>
        </div>

        <!-- Last meaningful contact -->
        <div class="sm:col-span-2 border-t border-gray-100 pt-3">
          <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Last meaningful contact') }}</label>
          <div v-if="editingField === 'micro_last_contact'">
            <div class="flex gap-2">
              <input
                v-model="editValue"
                type="date"
                class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <input
                v-model="lastContactTopic"
                type="text"
                :placeholder="__('Topic')"
                class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div class="mt-1 flex gap-1">
              <button class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700" @click="saveLastContact">{{ __('Save') }}</button>
              <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200" @click="cancelEdit">{{ __('Cancel') }}</button>
            </div>
          </div>
          <p
            v-else
            class="cursor-pointer rounded-md px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
            :class="{ 'italic text-gray-400': !c.micro_last_contact_date }"
            @click="startEditLastContact"
          >
            <template v-if="c.micro_last_contact_date">
              {{ c.micro_last_contact_date }}
              <span v-if="c.micro_last_contact_topic" class="text-gray-500"> — {{ c.micro_last_contact_topic }}</span>
            </template>
            <template v-else>{{ __('Click to set...') }}</template>
          </p>
        </div>
      </div>
    </div>

    <!-- Customer info grid -->
    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Contact Details') }}</h3>
        <dl class="space-y-2 text-sm">
          <div v-if="c.email_id">
            <dt class="text-gray-500">{{ __('Email') }}</dt>
            <dd class="text-gray-900">{{ c.email_id }}</dd>
          </div>
          <div v-if="c.phone">
            <dt class="text-gray-500">{{ __('Phone') }}</dt>
            <dd class="text-gray-900">{{ c.phone }}</dd>
          </div>
          <div v-if="c.mobile_no">
            <dt class="text-gray-500">{{ __('Mobile') }}</dt>
            <dd class="text-gray-900">{{ c.mobile_no }}</dd>
          </div>
          <div v-if="c.micro_website">
            <dt class="text-gray-500">{{ __('Website') }}</dt>
            <dd class="text-gray-900">{{ c.micro_website }}</dd>
          </div>
        </dl>
      </div>

      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Address') }}</h3>
        <dl class="space-y-2 text-sm">
          <div v-if="c.micro_address">
            <dd class="text-gray-900">{{ c.micro_address }}</dd>
          </div>
          <div v-if="c.micro_city || c.micro_postal_code">
            <dd class="text-gray-900">
              {{ [c.micro_postal_code, c.micro_city].filter(Boolean).join(' ') }}
            </dd>
          </div>
          <div v-if="c.micro_country">
            <dd class="text-gray-900">{{ c.micro_country }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <!-- Unified notes timeline -->
    <div v-if="customer.data.notes?.length" class="mb-6">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">{{ __('Notes') }}</h3>
        <a href="/dock/notes" class="text-sm text-gray-500 hover:text-gray-700">
          {{ __('All notes') }} &rarr;
        </a>
      </div>
      <div class="space-y-2">
        <a
          v-for="note in customer.data.notes"
          :key="note.name"
          :href="note.source === 'dock' ? '/dock/notes' : undefined"
          class="block rounded-lg border bg-white px-4 py-3 transition-colors"
          :class="[
            note.pinned ? 'border-blue-300 bg-blue-50/30' : 'border-gray-200',
            note.source === 'dock' ? 'hover:bg-gray-50 cursor-pointer' : '',
          ]"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="note.source === 'dock' ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600'"
              >
                {{ __(note.note_type) }}
              </span>
              <span v-if="note.pinned" class="text-xs text-blue-500">{{ __('Pinned') }}</span>
            </div>
            <span class="text-xs text-gray-400">{{ note.date }}</span>
          </div>
          <p v-if="note.subject" class="mt-1 text-sm font-medium text-gray-800">{{ note.subject }}</p>
          <p class="mt-0.5 text-sm text-gray-700" v-html="note.content" />
        </a>
      </div>
    </div>

  </div>
</template>
