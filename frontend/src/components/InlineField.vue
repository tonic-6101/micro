<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<!--
  One field of a record: reads as text, turns into an editor when clicked.
  `active` is shared between all fields of a page so only one is ever open.
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { __ } from '@/composables/useTranslate'
import FieldLabel from '@/components/FieldLabel.vue'

const props = withDefaults(
  defineProps<{
    /** Fieldname — what `active` is compared against, and what `save` reports. */
    name: string
    label?: string
    value?: string | number | null
    /** What the read view shows, when that is not the stored value itself. */
    display?: string
    type?: 'text' | 'textarea' | 'date' | 'number' | 'select'
    options?: { value: string; label: string }[]
    placeholder?: string
    rows?: number
    saving?: boolean
    error?: string
    readonly?: boolean
    /** Read view when there is nothing yet. */
    emptyLabel?: string
    /** Overrides the glossary entry `name` would otherwise resolve to. */
    hint?: string
  }>(),
  { type: 'text', rows: 3 },
)

const emit = defineEmits<{ save: [field: string, value: string] }>()

const active = defineModel<string | null>('active', { default: null })

const draft = ref('')

const editing = computed(() => active.value === props.name)
const readLabel = computed(() => {
  if (props.display) return props.display
  return props.value === undefined || props.value === null ? '' : String(props.value)
})

function start() {
  if (props.readonly) return
  draft.value = props.value === undefined || props.value === null ? '' : String(props.value)
  active.value = props.name
}

function cancel() {
  active.value = null
}

function save() {
  emit('save', props.name, draft.value)
}
</script>

<template>
  <div>
    <FieldLabel
      v-if="label"
      class="mb-1"
      :label="label"
      :field="name"
      :hint="hint"
      :uppercase="false"
    />

    <div v-if="editing">
      <select
        v-if="type === 'select'"
        v-model="draft"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        @keydown.escape="cancel"
      >
        <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
      </select>
      <textarea
        v-else-if="type === 'textarea'"
        v-model="draft"
        :rows="rows"
        :placeholder="placeholder"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        @keydown.escape="cancel"
      />
      <input
        v-else
        v-model="draft"
        :type="type"
        :placeholder="placeholder"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        @keyup.enter="save"
        @keydown.escape="cancel"
      />

      <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>

      <div class="mt-1 flex gap-1">
        <button
          type="button"
          class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
          :disabled="saving"
          @click="save"
        >
          {{ __('Save') }}
        </button>
        <button
          type="button"
          class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
          @click="cancel"
        >
          {{ __('Cancel') }}
        </button>
      </div>
    </div>

    <p
      v-else
      class="-mx-2 whitespace-pre-wrap rounded-md px-2 py-1.5 text-sm text-gray-900"
      :class="[readonly ? '' : 'cursor-pointer hover:bg-gray-50', readLabel ? '' : 'italic text-gray-400']"
      @click="start"
    >
      {{ readLabel || emptyLabel || __('Click to add...') }}
    </p>
  </div>
</template>
