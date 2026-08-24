<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import { MICRO_SOURCES } from '@/types/micro'
import type { MicroLead } from '@/types/micro'
import ContactPicker from '@/components/ContactPicker.vue'
import FieldLabel from '@/components/FieldLabel.vue'
import { expectedValueRange, maxExpectedValue } from '@/limits'

const props = defineProps<{
  pipeline: string
  /** Stage the card lands in. Omitted, the controller picks the first open one. */
  stage?: string
  stageName?: string
}>()

const emit = defineEmits<{
  close: []
  created: [lead: MicroLead]
}>()

const form = ref({
  lead_name: '',
  contact: '',
  priority: 'Medium',
  source: '',
  expected_value: '',
  next_follow_up: '',
  notes: '',
})

const contactLabel = ref('')
const nameTouched = ref(false)
const error = ref('')

// Shown under the amount — the answer to "0 to how much?"
const valueRange = computed(() => expectedValueRange())

const createLead = createResource({ url: 'micro.api.leads.create_lead' })

const isValid = computed(() => Boolean(form.value.lead_name.trim()))

// A lead is usually named after whoever it is with — fill it in, but never
// overwrite a name the user has typed themselves.
watch(contactLabel, (label) => {
  if (label && !nameTouched.value) {
    form.value.lead_name = label
  }
})

function submit() {
  if (!isValid.value) {
    error.value = __('Lead name is required')
    return
  }

  error.value = ''

  const params: Record<string, string | number> = {
    lead_name: form.value.lead_name.trim(),
    pipeline: props.pipeline,
    priority: form.value.priority,
  }

  if (props.stage) params.stage = props.stage
  if (form.value.contact) params.contact = form.value.contact
  if (form.value.source) params.source = form.value.source
  if (form.value.expected_value) params.expected_value = Number(form.value.expected_value)
  if (form.value.next_follow_up) params.next_follow_up = form.value.next_follow_up
  if (form.value.notes.trim()) params.notes = form.value.notes.trim()

  createLead
    .submit(params)
    .then((result: { lead: MicroLead }) => emit('created', result.lead))
    .catch((err: unknown) => {
      error.value =
        (err as { messages?: string[] })?.messages?.[0] || __('Failed to create lead')
    })
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      @click.self="emit('close')"
    >
      <div class="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
        <h2 class="text-base font-semibold text-gray-900">{{ __('New lead') }}</h2>
        <p class="mt-1 text-xs text-gray-500">
          {{
            stageName
              ? __('Lands in') + ' ' + __(stageName)
              : __('Lands in the first open stage of this pipeline.')
          }}
        </p>

        <div class="mt-4 space-y-3">
          <!-- Contact first: it names the lead for you -->
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">
              {{ __('Contact') }}
            </label>
            <ContactPicker v-model="form.contact" v-model:label="contactLabel" />
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">
              {{ __('Lead Name') }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.lead_name"
              type="text"
              :placeholder="__('What is this deal about?')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              @input="nameTouched = true"
              @keyup.enter="submit"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">
                {{ __('Priority') }}
              </label>
              <select
                v-model="form.priority"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700"
              >
                <option value="Low">{{ __('Low') }}</option>
                <option value="Medium">{{ __('Medium') }}</option>
                <option value="High">{{ __('High') }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">
                {{ __('Source') }}
              </label>
              <select
                v-model="form.source"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700"
              >
                <option value="">{{ __('Not set') }}</option>
                <option v-for="s in MICRO_SOURCES" :key="s" :value="s">{{ __(s) }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <FieldLabel
                field="expected_value"
                :label="__('Expected Value')"
                :uppercase="false"
                class="mb-1"
              />
              <input
                v-model="form.expected_value"
                type="number"
                min="0"
                :max="maxExpectedValue() || undefined"
                step="0.01"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
              <p v-if="valueRange" class="mt-1 text-xs text-gray-400">{{ valueRange }}</p>
            </div>
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">
                {{ __('Next Follow-up') }}
              </label>
              <input
                v-model="form.next_follow_up"
                type="date"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Notes') }}</label>
            <textarea
              v-model="form.notes"
              rows="2"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
        </div>

        <p v-if="error" class="mt-2 text-xs text-red-600">{{ error }}</p>

        <div class="mt-4 flex justify-end gap-2">
          <button
            type="button"
            class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            @click="emit('close')"
          >
            {{ __('Cancel') }}
          </button>
          <button
            type="button"
            class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
            :disabled="!isValid || createLead.loading"
            @click="submit"
          >
            {{ createLead.loading ? __('Creating...') : __('Create') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
