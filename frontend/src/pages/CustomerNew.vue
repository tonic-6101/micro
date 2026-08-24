<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import ContactPicker from '@/components/ContactPicker.vue'
import type { DuplicateMatch } from '@/types/micro'

const router = useRouter()

const form = ref({
  first_name: '',
  last_name: '',
  contact_type: 'Person' as 'Person' | 'Organization',
  status: 'Potential' as 'Potential' | 'Active' | 'Inactive',
  organization: '',
  organization_contact: '',
  email: '',
  phone: '',
  mobile: '',
  website: '',
  address: '',
  city: '',
  postal_code: '',
  country: '',
  source: '',
  notes: '',
})

const error = ref('')
const submitting = ref(false)
const organizationLabel = ref('')

const isPerson = computed(() => form.value.contact_type === 'Person')

const isValid = computed(() => {
  if (!form.value.first_name.trim()) return false
  if (isPerson.value && !form.value.last_name.trim()) return false
  return true
})

// Warn before the save, never block it. A solo business owner who is told "no"
// by their own CRM has nobody to appeal to — and sometimes two people really do
// share a name.
const duplicateHint = ref<DuplicateMatch[]>([])
const hintDismissed = ref(false)
let checkTimer: ReturnType<typeof setTimeout> | undefined

const duplicateCheck = createResource({
  url: 'micro.api.duplicates.check_duplicates',
  onSuccess(data: { matches: DuplicateMatch[] }) {
    // Only the confident bands are worth interrupting someone mid-form for.
    duplicateHint.value = data.matches.filter((match) => match.band === 'Certain' || match.band === 'Likely')
  },
  onError() {
    duplicateHint.value = []
  },
})

watch(
  () => [form.value.first_name, form.value.last_name, form.value.email, form.value.phone, form.value.organization],
  () => {
    hintDismissed.value = false
    clearTimeout(checkTimer)

    const hasEnough =
      form.value.email.trim() || form.value.phone.trim() || form.value.first_name.trim().length >= 3
    if (!hasEnough) {
      duplicateHint.value = []
      return
    }

    checkTimer = setTimeout(() => {
      duplicateCheck.submit({
        first_name: form.value.first_name.trim() || undefined,
        last_name: form.value.last_name.trim() || undefined,
        email: form.value.email.trim() || undefined,
        phone: form.value.phone.trim() || undefined,
        mobile: form.value.mobile.trim() || undefined,
        organization: form.value.organization.trim() || organizationLabel.value || undefined,
        contact_type: form.value.contact_type,
        postal_code: form.value.postal_code.trim() || undefined,
        address: form.value.address.trim() || undefined,
        website: form.value.website.trim() || undefined,
      })
    }, 400)
  },
)

onUnmounted(() => clearTimeout(checkTimer))

const createCustomer = createResource({
  url: 'micro.api.customers.create_customer',
  onSuccess(data: { customer: { name: string } }) {
    router.push(`/micro/customers/${data.customer.name}`)
  },
  onError(err: { messages?: string[] }) {
    submitting.value = false
    error.value = err.messages?.[0] || __('Failed to create customer')
  },
})

function submit() {
  if (!form.value.first_name.trim()) {
    error.value = isPerson.value ? __('First name is required') : __('Company name is required')
    return
  }
  if (isPerson.value && !form.value.last_name.trim()) {
    error.value = __('Last name is required')
    return
  }

  error.value = ''
  submitting.value = true

  const params: Record<string, string> = {
    first_name: form.value.first_name.trim(),
    contact_type: form.value.contact_type,
    status: form.value.status,
  }

  if (form.value.last_name.trim()) params.last_name = form.value.last_name.trim()
  if (form.value.email.trim()) params.email = form.value.email.trim()
  if (form.value.phone.trim()) params.phone = form.value.phone.trim()
  if (form.value.mobile.trim()) params.mobile = form.value.mobile.trim()
  if (form.value.website.trim()) params.website = form.value.website.trim()
  if (form.value.organization_contact) params.organization_contact = form.value.organization_contact
  else if (form.value.organization.trim()) params.organization = form.value.organization.trim()
  if (form.value.source) params.source = form.value.source
  if (form.value.address.trim()) params.address = form.value.address.trim()
  if (form.value.city.trim()) params.city = form.value.city.trim()
  if (form.value.postal_code.trim()) params.postal_code = form.value.postal_code.trim()
  if (form.value.country.trim()) params.country = form.value.country.trim()
  if (form.value.notes.trim()) params.notes = form.value.notes.trim()

  createCustomer.submit(params)
}

const sources = [
  'Manual', 'Google Ads', 'Facebook', 'Instagram', 'LinkedIn',
  'Email Campaign', 'Cold Call', 'Web Form', 'Organic Search',
  'Referral', 'Partner', 'Event', 'Import', 'Other',
]
const statuses = ['Potential', 'Active', 'Inactive']
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3">
        <router-link
          to="/micro/customers"
          class="text-sm text-gray-500 hover:text-gray-700"
        >
          {{ __('Customers') }}
        </router-link>
        <span class="text-gray-300">/</span>
        <span class="text-sm text-gray-700">{{ __('New Customer') }}</span>
      </div>

      <div class="mt-2 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">
          {{ __('New Customer') }}
        </h1>
        <div class="flex items-center gap-3">
          <router-link
            to="/micro/customers"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {{ __('Cancel') }}
          </router-link>
          <button
            :disabled="!isValid || submitting"
            class="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
            @click="submit"
          >
            {{ submitting ? __('Saving...') : __('Save Customer') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 rounded-md bg-red-50 p-3">
      <p class="text-sm text-red-700">{{ error }}</p>
    </div>

    <!-- Possible duplicate, found while typing -->
    <div
      v-if="duplicateHint.length && !hintDismissed"
      class="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4"
    >
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0">
          <p class="text-sm font-medium text-amber-900">
            {{ __('This contact may already exist') }}
          </p>
          <ul class="mt-2 space-y-2">
            <li v-for="match in duplicateHint" :key="match.contact.name" class="text-sm">
              <router-link
                :to="`/micro/customers/${match.contact.name}`"
                class="font-medium text-amber-900 underline hover:text-amber-700"
              >
                {{ match.contact.full_name || match.contact.name }}
              </router-link>
              <span class="text-amber-800">
                · {{ [match.contact.email_id, match.contact.phone].filter(Boolean).join(' · ') }}
              </span>
              <span class="block text-xs text-amber-700">{{ match.reasons.join(' · ') }}</span>
            </li>
          </ul>
        </div>
        <button
          class="shrink-0 text-xs font-medium text-amber-900 underline hover:text-amber-700"
          @click="hintDismissed = true"
        >
          {{ __('Create anyway') }}
        </button>
      </div>
    </div>

    <!-- Form -->
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <!-- Basic Info -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Basic Info') }}</h3>

        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Contact Type') }} <span class="text-red-500">*</span>
            </label>
            <select
              v-model="form.contact_type"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            >
              <option value="Person">{{ __('Person') }}</option>
              <option value="Organization">{{ __('Organization') }}</option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Status') }} <span class="text-red-500">*</span>
            </label>
            <select
              v-model="form.status"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            >
              <option v-for="s in statuses" :key="s" :value="s">
                {{ __(s) }}
              </option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ isPerson ? __('First Name') : __('Company Name') }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.first_name"
              type="text"
              :placeholder="isPerson ? __('First Name') : __('Company Name')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>

          <div v-if="isPerson">
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Last Name') }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.last_name"
              type="text"
              :placeholder="__('Last Name')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>

          <!-- Pick the organization record when there is one, so the person is
               really attached to it; otherwise the typed name is kept as before. -->
          <div v-if="isPerson">
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Organization') }}
            </label>
            <ContactPicker
              v-model="form.organization_contact"
              v-model:label="organizationLabel"
              contact-type="Organization"
              :placeholder="__('Search organizations...')"
            />
            <div v-if="!form.organization_contact" class="mt-2">
              <input
                v-model="form.organization"
                type="text"
                :placeholder="__('...or just type the company name')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
              <p class="mt-1 text-xs text-gray-400">
                {{ __('A typed name is only text. Pick an organization to link them properly.') }}
              </p>
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Source') }}
            </label>
            <select
              v-model="form.source"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            >
              <option value="">{{ __('Select...') }}</option>
              <option v-for="src in sources" :key="src" :value="src">
                {{ __(src) }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <!-- Contact Details -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Contact Details') }}</h3>

        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Email') }}
            </label>
            <input
              v-model="form.email"
              type="email"
              :placeholder="__('Email')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Phone') }}
            </label>
            <input
              v-model="form.phone"
              type="tel"
              :placeholder="__('Phone')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Mobile') }}
            </label>
            <input
              v-model="form.mobile"
              type="tel"
              :placeholder="__('Mobile')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Website') }}
            </label>
            <input
              v-model="form.website"
              type="url"
              :placeholder="__('Website')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
        </div>
      </div>

      <!-- Address -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Address') }}</h3>

        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Address') }}
            </label>
            <input
              v-model="form.address"
              type="text"
              :placeholder="__('Street address')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">
                {{ __('Postal Code') }}
              </label>
              <input
                v-model="form.postal_code"
                type="text"
                :placeholder="__('Postal Code')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">
                {{ __('City') }}
              </label>
              <input
                v-model="form.city"
                type="text"
                :placeholder="__('City')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Country') }}
            </label>
            <input
              v-model="form.country"
              type="text"
              :placeholder="__('Country')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
        </div>
      </div>

      <!-- Notes -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Notes') }}</h3>

        <div>
          <textarea
            v-model="form.notes"
            rows="6"
            :placeholder="__('Additional notes...')"
            class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
          ></textarea>
        </div>
      </div>
    </div>
  </div>
</template>
