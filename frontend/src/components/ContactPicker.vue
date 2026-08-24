<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { CustomersListResponse, MicroCustomer } from '@/types/micro'

const model = defineModel<string>({ default: '' })

/** Display name of the selected contact. The picker cannot resolve a docname
    on its own, so the caller seeds it — and reads it back to label the choice. */
const selectedLabel = defineModel<string>('label', { default: '' })

// `contactType` narrows the search to people or to organizations. Left unset,
// the picker searches everything, which is what the lead pickers want.
const props = defineProps<{ placeholder?: string; contactType?: 'Person' | 'Organization' }>()

const PAGE_LENGTH = 10

const search = ref('')
const showDropdown = ref(false)
let debounce: ReturnType<typeof setTimeout> | undefined

// Searched on the server: a contact book outgrows the client-side filter that
// CategoryPicker can afford.
const contacts = createResource({
  url: 'micro.api.customers.get_customers',
  params: { limit_page_length: PAGE_LENGTH, contact_type: props.contactType },
  auto: true,
  transform(data: CustomersListResponse) {
    return data.customers
  },
})

const results = computed<MicroCustomer[]>(() => contacts.data || [])

const displayLabel = computed(() => selectedLabel.value || model.value)

function contactLabel(contact: MicroCustomer): string {
  return contact.full_name || contact.company_name || contact.name
}

function contactHint(contact: MicroCustomer): string {
  return [contact.company_name !== contact.full_name ? contact.company_name : '', contact.email_id]
    .filter(Boolean)
    .join(' · ')
}

// The model can be cleared by the parent (form reset) — drop the stale label.
watch(model, (value) => {
  if (!value) selectedLabel.value = ''
})

watch(search, (value) => {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    contacts.update({
      params: {
        search: value.trim() || undefined,
        limit_page_length: PAGE_LENGTH,
        contact_type: props.contactType,
      },
    })
    contacts.reload()
  }, 250)
})

onBeforeUnmount(() => clearTimeout(debounce))

function selectContact(contact: MicroCustomer) {
  model.value = contact.name
  selectedLabel.value = contactLabel(contact)
  search.value = ''
  showDropdown.value = false
}

function clearContact() {
  model.value = ''
  selectedLabel.value = ''
  search.value = ''
}

function onFocus() {
  showDropdown.value = true
  search.value = ''
}

function onBlur() {
  // Delay to allow click on dropdown items
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}
</script>

<template>
  <div class="relative">
    <!-- Selected state -->
    <div v-if="model && !showDropdown" class="flex items-center gap-2">
      <div
        class="flex-1 cursor-pointer truncate rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
        @click="onFocus"
      >
        {{ displayLabel }}
      </div>
      <button
        type="button"
        class="text-gray-400 hover:text-gray-600"
        :title="__('Clear')"
        @click="clearContact"
      >
        &times;
      </button>
    </div>

    <!-- Search input -->
    <input
      v-else
      v-model="search"
      type="text"
      :placeholder="placeholder || __('Search contacts...')"
      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      @focus="onFocus"
      @blur="onBlur"
    />

    <!-- Dropdown -->
    <div
      v-if="showDropdown"
      class="absolute z-10 mt-1 max-h-56 w-full overflow-auto rounded-md border border-gray-200 bg-white shadow-lg"
    >
      <div
        v-for="contact in results"
        :key="contact.name"
        class="cursor-pointer px-3 py-2 hover:bg-gray-50"
        @mousedown.prevent="selectContact(contact)"
      >
        <p class="text-sm text-gray-900">{{ contactLabel(contact) }}</p>
        <p v-if="contactHint(contact)" class="truncate text-xs text-gray-500">
          {{ contactHint(contact) }}
        </p>
      </div>

      <div v-if="contacts.loading" class="px-3 py-2 text-sm text-gray-400">
        {{ __('Loading...') }}
      </div>
      <div v-else-if="!results.length" class="px-3 py-2 text-sm text-gray-400">
        {{ __('No contacts found') }}
      </div>

      <router-link
        to="/micro/customers/new"
        class="block border-t border-gray-100 px-3 py-2 text-sm font-medium text-accent-600 hover:bg-accent-50"
      >
        {{ __('New contact') }} &rarr;
      </router-link>
    </div>
  </div>
</template>
