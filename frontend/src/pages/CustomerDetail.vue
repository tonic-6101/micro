<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CapacityWidget from '@/components/CapacityWidget.vue'
import ContactPicker from '@/components/ContactPicker.vue'
import InlineField from '@/components/InlineField.vue'
import { MICRO_SOURCES } from '@/types/micro'
import type {
  CustomerDeletePreview,
  CustomerDetailResponse,
  CustomerLead,
  MicroCustomer,
  OrganizationMember,
  SegmentsListResponse,
} from '@/types/micro'

const props = defineProps<{
  id: string
}>()

const router = useRouter()

const customer = createResource({
  url: 'micro.api.customers.get_customer',
  params: { customer_id: props.id },
  auto: true,
  transform(data: CustomerDetailResponse) {
    return data
  },
})

// "Delete" is two different requests. Removing takes the contact out of Micro
// and leaves every document standing; erasing destroys the record, and is only
// offered when nothing has to be kept. The dialog asks the server which of the
// two is even available before showing the buttons.
const deleteOpen = ref(false)
const deleteError = ref('')
const deleting = ref('')

const deletePreview = createResource({
  url: 'micro.api.customers.get_delete_preview',
  transform(data: CustomerDeletePreview) {
    return data
  },
})

const deleteCustomer = createResource({
  url: 'micro.api.customers.delete_customer',
  onSuccess() {
    deleting.value = ''
    deleteOpen.value = false
    router.push('/micro/customers')
  },
  onError(err: { messages?: string[] }) {
    deleting.value = ''
    deleteError.value = err.messages?.[0] || __('Could not delete this customer')
  },
})

function openDelete() {
  deleteError.value = ''
  deleteOpen.value = true
  deletePreview.submit({ customer_id: props.id })
}

function runDelete(mode: 'remove' | 'erase') {
  deleteError.value = ''
  deleting.value = mode
  deleteCustomer.submit({ customer_id: props.id, mode })
}

const deleteCounts = computed(() =>
  Object.entries(deletePreview.data?.deletes || {})
    .map(([doctype, count]) => [doctype, Number(count)] as [string, number])
    .filter(([, count]) => count > 0),
)

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

// --- the contact's own fields ---------------------------------------------
// Everything the record itself carries: how to reach them, where they are,
// and how they are filed. Same click-to-edit as the intelligence card above.

const detailError = ref('')

const updateCustomer = createResource({
  url: 'micro.api.customers.update_customer',
  onSuccess() {
    editingField.value = null
    customer.reload()
  },
  onError(err: { messages?: string[] }) {
    detailError.value = err.messages?.[0] || __('Failed to update customer')
  },
})

// Segments are user-defined, so the options come from the site, not the code.
const segments = createResource({
  url: 'micro.api.pipeline.get_segments',
  auto: true,
  transform(data: SegmentsListResponse) {
    return data.segments
  },
})

const statusOptions = computed(() =>
  ['Potential', 'Active', 'Inactive'].map((value) => ({ value, label: __(value) })),
)

const sourceOptions = computed(() => [
  { value: '', label: __('Not set') },
  ...MICRO_SOURCES.map((value) => ({ value, label: __(value) })),
])

const segmentOptions = computed(() => [
  { value: '', label: __('Not set') },
  ...(segments.data || []).map((s: { name: string; segment_name: string }) => ({
    value: s.name,
    label: s.segment_name,
  })),
])

const segmentLabel = computed(
  () =>
    segmentOptions.value.find((opt) => opt.value === c.value?.micro_segment)?.label ||
    c.value?.micro_segment ||
    '',
)

function saveDetail(field: string, value: string) {
  detailError.value = ''
  updateCustomer.submit({ customer_id: props.id, [field]: value })
}

// --- tags ------------------------------------------------------------------
// The many labels a contact can carry, next to the one segment it belongs to.
// Storage is Frappe's (`Tag`, `Tag Link`, `_user_tags`) — Micro adds no table.

const tags = computed<string[]>(() => customer.data?.tags || [])
const newTag = ref('')
const addingTag = ref(false)

const addTag = createResource({
  url: 'micro.api.customers.add_customer_tag',
  onSuccess() {
    newTag.value = ''
    addingTag.value = false
    customer.reload()
  },
})

const removeTag = createResource({
  url: 'micro.api.customers.remove_customer_tag',
  onSuccess() {
    customer.reload()
  },
})

function onAddTag() {
  const tag = newTag.value.trim()
  if (!tag) {
    addingTag.value = false
    return
  }
  addTag.submit({ customer_id: props.id, tag })
}

// --- organization ----------------------------------------------------------

const organization = computed(() => customer.data?.organization || null)
const members = computed<OrganizationMember[]>(() => customer.data?.members || [])
const isOrganization = computed(() => c.value?.micro_contact_type === 'Organization')

// Most contacts predate the link and carry only a typed employer, so attaching
// one after the fact is the common case — not something only the create form
// can do.
const editingOrganization = ref(false)
const organizationChoice = ref('')
const organizationChoiceLabel = ref('')

const saveOrganization = createResource({
  url: 'micro.api.customers.set_customer_organization',
  onSuccess() {
    editingOrganization.value = false
    organizationChoice.value = ''
    organizationChoiceLabel.value = ''
    customer.reload()
  },
})

function startEditingOrganization() {
  organizationChoice.value = organization.value?.name || ''
  organizationChoiceLabel.value = organization.value
    ? organization.value.company_name || organization.value.full_name || ''
    : ''
  editingOrganization.value = true
}

function onSaveOrganization() {
  // An empty choice is a detach, which the endpoint accepts as null.
  saveOrganization.submit({ customer_id: props.id, organization: organizationChoice.value || null })
}

// --- leads -----------------------------------------------------------------
// A contact can be open in several pipelines at once, and can go through the
// same pipeline again years later. Both halves matter here: what is running
// now, and how the earlier attempts ended.

const leads = computed<CustomerLead[]>(() => customer.data?.leads || [])
const openLeads = computed(() => leads.value.filter((lead) => lead.is_open))
const pastLeads = computed(() => leads.value.filter((lead) => !lead.is_open))

const leadStatusClasses: Record<string, string> = {
  Open: 'bg-blue-100 text-blue-800',
  Won: 'bg-green-100 text-green-800',
  Lost: 'bg-red-100 text-red-800',
  Archived: 'bg-gray-100 text-gray-600',
}

function leadValue(lead: CustomerLead): string {
  if (!lead.expected_value) return ''
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(lead.expected_value)
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

        <!-- Tags: as many as the contact needs, each removable on the spot -->
        <div class="mt-2 flex flex-wrap items-center gap-1">
          <span
            v-for="tag in tags"
            :key="tag"
            class="group inline-flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
          >
            {{ tag }}
            <button
              type="button"
              class="text-gray-400 hover:text-red-600"
              :title="__('Remove tag')"
              @click="removeTag.submit({ customer_id: props.id, tag })"
            >
              &times;
            </button>
          </span>
          <input
            v-if="addingTag"
            v-model="newTag"
            type="text"
            :placeholder="__('Tag name')"
            class="w-32 rounded border border-gray-300 px-2 py-0.5 text-xs focus:border-gray-500 focus:outline-none"
            autofocus
            @keyup.enter="onAddTag"
            @keydown.escape="addingTag = false"
            @blur="onAddTag"
          />
          <button
            v-else
            type="button"
            class="rounded px-1.5 py-0.5 text-xs text-gray-400 hover:text-gray-700"
            @click="addingTag = true"
          >
            + {{ __('Tag') }}
          </button>
        </div>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <a
          :href="`/app/contact/${props.id}`"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          {{ __('Edit in Desk') }}
        </a>
        <button
          type="button"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-red-50 hover:text-red-700"
          @click="openDelete"
        >
          {{ __('Delete') }}
        </button>
      </div>
    </div>

    <!-- Capacity hint for potential customers -->
    <CapacityWidget v-if="c.micro_status === 'Potential'" :compact="true" class="mb-4" />

    <!-- The other side of the relation: a person's employer, or an
         organization's people. Free text could never answer either. -->
    <div class="mb-6 rounded-lg border border-gray-200 bg-white p-5">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">
          {{ isOrganization ? __('People') : __('Organization') }}
        </h3>
        <span v-if="isOrganization && members.length" class="text-xs text-gray-500">
          {{ members.length }}
        </span>
        <button
          v-else-if="!isOrganization && !editingOrganization"
          type="button"
          class="text-xs font-medium text-accent-600 hover:text-accent-700"
          @click="startEditingOrganization"
        >
          {{ organization ? __('Change') : __('Link') }}
        </button>
      </div>

      <!-- Person → the organization they belong to -->
      <template v-if="!isOrganization">
        <div v-if="editingOrganization">
          <ContactPicker
            v-model="organizationChoice"
            v-model:label="organizationChoiceLabel"
            contact-type="Organization"
            :placeholder="__('Search organizations...')"
          />
          <div class="mt-3 flex items-center gap-2">
            <button
              type="button"
              class="rounded-md bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-800 disabled:opacity-50"
              :disabled="saveOrganization.loading"
              @click="onSaveOrganization"
            >
              {{ saveOrganization.loading ? __('Saving...') : __('Save') }}
            </button>
            <button
              type="button"
              class="px-2 py-1.5 text-xs text-gray-500 hover:text-gray-700"
              @click="editingOrganization = false"
            >
              {{ __('Cancel') }}
            </button>
          </div>
          <!-- Clearing the picker and saving is how a person is detached. -->
          <p class="mt-2 text-xs text-gray-400">
            {{ __('Clear the field and save to detach them.') }}
          </p>
        </div>

        <router-link
          v-else-if="organization"
          :to="`/micro/customers/${organization.name}`"
          class="block rounded-lg border border-gray-100 px-3 py-2 hover:bg-gray-50"
        >
          <p class="text-sm font-medium text-gray-900">
            {{ organization.company_name || organization.full_name }}
          </p>
          <p class="mt-0.5 text-xs text-gray-500">
            {{ [organization.micro_city, organization.email_id, organization.phone].filter(Boolean).join(' · ') || __('Open') }}
          </p>
        </router-link>

        <!-- A typed employer is all most contacts have; say so plainly rather
             than pretending the relation is empty. -->
        <div v-else>
          <p v-if="c.company_name" class="text-sm text-gray-900">{{ c.company_name }}</p>
          <p class="text-xs italic text-gray-400" :class="c.company_name ? 'mt-0.5' : ''">
            {{ c.company_name ? __('Typed by hand — not linked to an organization record.') : __('No organization linked.') }}
          </p>
        </div>
      </template>

      <!-- Organization → the people who belong to it -->
      <template v-else-if="isOrganization">
        <p v-if="!members.length" class="text-sm italic text-gray-400">
          {{ __('Nobody is linked to this organization yet.') }}
        </p>
        <div v-else class="space-y-2">
          <router-link
            v-for="member in members"
            :key="member.name"
            :to="`/micro/customers/${member.name}`"
            class="block rounded-lg border border-gray-100 px-3 py-2 hover:bg-gray-50"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-gray-900">{{ member.full_name }}</p>
                <p class="mt-0.5 truncate text-xs text-gray-500">
                  {{ [member.designation, member.email_id, member.phone || member.mobile_no].filter(Boolean).join(' · ') }}
                </p>
              </div>
              <span
                v-if="member.micro_status"
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="statusClasses[member.micro_status] || 'bg-gray-100 text-gray-600'"
              >
                {{ __(member.micro_status) }}
              </span>
            </div>
          </router-link>
        </div>
      </template>
    </div>

    <!-- Leads: what is running in which pipeline, and how earlier runs ended -->
    <div class="mb-6 rounded-lg border border-gray-200 bg-white p-4">
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">{{ __('Leads') }}</h3>
        <router-link to="/micro/pipeline" class="text-sm text-gray-500 hover:text-gray-700">
          {{ __('Pipeline View') }} &rarr;
        </router-link>
      </div>

      <p v-if="!leads.length" class="text-sm italic text-gray-400">
        {{ __('Not in any pipeline yet. Add this contact to a pipeline from the board.') }}
      </p>

      <div v-else class="space-y-2">
        <router-link
          v-for="lead in openLeads"
          :key="lead.name"
          :to="`/micro/leads/${lead.name}`"
          class="block rounded-lg border border-gray-200 px-3 py-2 hover:bg-gray-50"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-gray-900">{{ lead.lead_name }}</p>
              <p class="mt-0.5 text-xs text-gray-500">
                {{ lead.pipeline_name || lead.pipeline || __('No pipeline') }}
                <span v-if="lead.stage_name"> · {{ __(lead.stage_name) }}</span>
                <span v-if="lead.next_follow_up"> · {{ __('Next Follow-up') }}: {{ lead.next_follow_up }}</span>
              </p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <span v-if="leadValue(lead)" class="text-xs text-gray-500">{{ leadValue(lead) }}</span>
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="leadStatusClasses[lead.status]"
              >
                {{ __(lead.status) }}
              </span>
            </div>
          </div>
        </router-link>

        <!-- History: what happened the last time this pipeline was run on them -->
        <details v-if="pastLeads.length" class="pt-1">
          <summary class="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
            {{ pastLeads.length }} {{ __('closed') }}
          </summary>
          <div class="mt-2 space-y-2">
            <router-link
              v-for="lead in pastLeads"
              :key="lead.name"
              :to="`/micro/leads/${lead.name}`"
              class="block rounded-lg border border-gray-100 bg-gray-50/60 px-3 py-2 hover:bg-gray-50"
            >
              <div class="flex flex-wrap items-center justify-between gap-2">
                <div class="min-w-0">
                  <p class="truncate text-sm text-gray-700">{{ lead.lead_name }}</p>
                  <p class="mt-0.5 text-xs text-gray-500">
                    {{ lead.pipeline_name || lead.pipeline || __('No pipeline') }}
                    <span v-if="lead.lost_reason"> · {{ lead.lost_reason }}</span>
                    <span v-if="lead.modified"> · {{ String(lead.modified).slice(0, 10) }}</span>
                  </p>
                </div>
                <span
                  class="inline-flex shrink-0 rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="leadStatusClasses[lead.status]"
                >
                  {{ lead.status === 'Archived' ? __('In trash') : __(lead.status) }}
                </span>
              </div>
            </router-link>
          </div>
        </details>
      </div>
    </div>

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

    <!-- Customer info grid — every field is here whether or not it is filled in -->
    <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div class="rounded-lg border border-gray-200 bg-white p-4">
        <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Contact Details') }}</h3>
        <div class="space-y-3">
          <InlineField
            v-model:active="editingField"
            name="first_name"
            :label="c.micro_contact_type === 'Organization' ? __('Organization Name') : __('First Name')"
            :value="c.first_name"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
          <InlineField
            v-if="c.micro_contact_type !== 'Organization'"
            v-model:active="editingField"
            name="last_name"
            :label="__('Last Name')"
            :value="c.last_name"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
          <InlineField
            v-model:active="editingField"
            name="company_name"
            :label="__('Organization')"
            :value="c.company_name"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
          <InlineField
            v-model:active="editingField"
            name="email_id"
            :label="__('Email')"
            :value="c.email_id"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
          <InlineField
            v-model:active="editingField"
            name="phone"
            :label="__('Phone')"
            :value="c.phone"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
          <InlineField
            v-model:active="editingField"
            name="mobile_no"
            :label="__('Mobile')"
            :value="c.mobile_no"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
          <InlineField
            v-model:active="editingField"
            name="micro_website"
            :label="__('Website')"
            :value="c.micro_website"
            :saving="updateCustomer.loading"
            :error="detailError"
            @save="saveDetail"
          />
        </div>
      </div>

      <div class="space-y-4">
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Address') }}</h3>
          <div class="space-y-3">
            <InlineField
              v-model:active="editingField"
              name="micro_address"
              :label="__('Street Address')"
              :value="c.micro_address"
              type="textarea"
              :rows="2"
              :saving="updateCustomer.loading"
              :error="detailError"
              @save="saveDetail"
            />
            <div class="grid grid-cols-2 gap-3">
              <InlineField
                v-model:active="editingField"
                name="micro_postal_code"
                :label="__('Postal Code')"
                :value="c.micro_postal_code"
                :saving="updateCustomer.loading"
                :error="detailError"
                @save="saveDetail"
              />
              <InlineField
                v-model:active="editingField"
                name="micro_city"
                :label="__('City')"
                :value="c.micro_city"
                :saving="updateCustomer.loading"
                :error="detailError"
                @save="saveDetail"
              />
            </div>
            <InlineField
              v-model:active="editingField"
              name="micro_country"
              :label="__('Country')"
              :value="c.micro_country"
              :saving="updateCustomer.loading"
              :error="detailError"
              @save="saveDetail"
            />
          </div>
        </div>

        <!-- How this contact is filed — the badges in the header, editable -->
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Classification') }}</h3>
          <div class="grid grid-cols-2 gap-3">
            <InlineField
              v-model:active="editingField"
              name="micro_status"
              :label="__('Status')"
              :value="c.micro_status"
              :display="__(c.micro_status)"
              type="select"
              :options="statusOptions"
              :saving="updateCustomer.loading"
              :error="detailError"
              @save="saveDetail"
            />
            <InlineField
              v-model:active="editingField"
              name="micro_source"
              :label="__('Source')"
              :value="c.micro_source"
              :display="c.micro_source ? __(c.micro_source) : ''"
              type="select"
              :options="sourceOptions"
              :empty-label="__('Click to set...')"
              :saving="updateCustomer.loading"
              :error="detailError"
              @save="saveDetail"
            />
            <InlineField
              v-model:active="editingField"
              name="micro_segment"
              :label="__('Segment')"
              :value="c.micro_segment"
              :display="segmentLabel"
              type="select"
              :options="segmentOptions"
              :empty-label="__('Click to set...')"
              :saving="updateCustomer.loading"
              :error="detailError"
              @save="saveDetail"
            />
            <div>
              <label class="mb-1 block text-xs font-medium text-gray-500">
                {{ __('Pipeline Stage') }}
              </label>
              <!-- Derived from the contact's open lead — edit the lead, not this -->
              <p class="-mx-2 px-2 py-1.5 text-sm" :class="c.micro_pipeline_stage ? 'text-gray-900' : 'italic text-gray-400'">
                {{ c.micro_pipeline_stage || __('Not set') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- The contact's own notes — what an import or the intake form wrote down -->
    <div class="mb-6 rounded-lg border border-gray-200 bg-white p-4">
      <h3 class="mb-3 text-sm font-medium text-gray-500">{{ __('Notes') }}</h3>
      <InlineField
        v-model:active="editingField"
        name="micro_notes"
        :value="c.micro_notes"
        type="textarea"
        :rows="5"
        :placeholder="__('What is worth remembering about this contact...')"
        :saving="updateCustomer.loading"
        :error="detailError"
        @save="saveDetail"
      />
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

    <!-- Delete: two requests wearing one word, so both are spelled out -->
    <div
      v-if="deleteOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      @click.self="deleteOpen = false"
    >
      <div class="w-full max-w-lg rounded-xl bg-white p-5 shadow-xl">
        <h2 class="text-base font-semibold text-gray-900">
          {{ __('Delete') }} {{ c.full_name }}
        </h2>

        <p v-if="deletePreview.loading" class="mt-4 text-sm text-gray-500">
          {{ __('Checking what depends on this customer...') }}
        </p>

        <div v-else-if="deletePreview.data" class="mt-4 space-y-4">
          <div v-if="deleteError" class="rounded-md bg-red-50 p-3">
            <p class="text-sm text-red-700">{{ deleteError }}</p>
          </div>

          <!-- Remove -->
          <div class="rounded-lg border border-gray-200 p-4">
            <p class="text-sm font-medium text-gray-900">{{ __('Remove from Micro') }}</p>
            <p class="mt-1 text-sm text-gray-500">
              {{ __('Stops being a customer and frees a slot under your limit. Every document stays, and the contact remains available to your other apps. You can add them back later.') }}
            </p>
            <button
              type="button"
              :disabled="Boolean(deleting)"
              class="mt-3 rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
              @click="runDelete('remove')"
            >
              {{ deleting === 'remove' ? __('Removing...') : __('Remove from Micro') }}
            </button>
          </div>

          <!-- Erase -->
          <div class="rounded-lg border border-gray-200 p-4">
            <p class="text-sm font-medium text-gray-900">{{ __('Delete permanently') }}</p>

            <template v-if="deletePreview.data.can_erase">
              <p class="mt-1 text-sm text-gray-500">
                {{ __('Erases the contact record itself. This cannot be undone.') }}
              </p>
              <ul v-if="deleteCounts.length" class="mt-2 space-y-0.5 text-sm text-gray-600">
                <li v-for="[doctype, count] in deleteCounts" :key="doctype">
                  · {{ count }} × {{ __(doctype) }} {{ __('will be deleted too') }}
                </li>
              </ul>
              <button
                type="button"
                :disabled="Boolean(deleting)"
                class="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
                @click="runDelete('erase')"
              >
                {{ deleting === 'erase' ? __('Deleting...') : __('Delete permanently') }}
              </button>
            </template>

            <template v-else>
              <p class="mt-1 text-sm text-gray-500">
                {{ __('Not possible for this customer:') }}
              </p>
              <ul class="mt-2 space-y-0.5 text-sm text-gray-600">
                <li v-for="item in deletePreview.data.retention_blockers" :key="item.doctype">
                  · {{ item.count }} × {{ __(item.doctype) }} — {{ __('has to be kept') }}
                </li>
                <li v-for="item in deletePreview.data.foreign_links" :key="item.doctype">
                  · {{ item.count }} × {{ __(item.doctype) }} — {{ __('used by another app') }}
                </li>
              </ul>
              <p class="mt-2 text-xs text-gray-500">
                {{ __('Remove the customer from Micro instead — the documents keep their recipient.') }}
              </p>
            </template>
          </div>
        </div>

        <div class="mt-5 flex justify-end">
          <button
            type="button"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            @click="deleteOpen = false"
          >
            {{ __('Cancel') }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>
