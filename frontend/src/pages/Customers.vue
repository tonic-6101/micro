<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import FieldLabel from '@/components/FieldLabel.vue'
import { NO_SEGMENT } from '@/types/micro'
import type { BulkDeleteResult, CustomerFacets, MicroCustomer } from '@/types/micro'

const router = useRouter()
const search = ref('')
const page = ref(1)
const pageSize = 20

// Two axes, and they answer different questions. The segment is the one
// durable category a contact belongs to ("Architekt"), so it sits in front as
// chips with counts. Tags are the many ad-hoc labels a contact may carry
// ("Altbau", "Messe 2026") and share the drawer with the rarer filters.
const segmentFilter = ref('')
const tagFilter = ref('')
const sourceFilter = ref('')
const showFilters = ref(false)

// Who to approach next. The same contact can be open in one pipeline, finished
// with another and untouched by a third, so "already a customer" is not the
// question — "already in *this* pipeline" is.
const pipelineFilter = ref('')
const pipelineState = ref('never')

const pipelines = createResource({
  url: 'micro.api.pipeline.get_pipelines',
  auto: true,
})

const pipelineStates = [
  { value: 'never', label: 'Never in it' },
  { value: 'open', label: 'Open in it' },
  { value: 'ever', label: 'Ever in it' },
]

const sources = [
  'Manual', 'Google Ads', 'Facebook', 'Instagram', 'LinkedIn',
  'Email Campaign', 'Cold Call', 'Web Form', 'Organic Search',
  'Referral', 'Partner', 'Event', 'Import', 'Other',
]

// The iPhone's "Duplicates Found" banner, in Micro: present when there is
// something to review, absent otherwise, and never in the way of the list.
const duplicates = createResource({
  url: 'micro.api.duplicates.get_duplicate_summary',
  auto: true,
})

// Segments and tags with their counts. Reloaded after a filtered fetch so the
// chips stay honest when a contact is refiled elsewhere in the app.
const facets = createResource({
  url: 'micro.api.customers.get_customer_facets',
  auto: true,
  transform(data: CustomerFacets) {
    return data
  },
})

const customers = createResource({
  url: 'micro.api.customers.get_customers',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { customers: MicroCustomer[]; total: number }) {
    return data
  },
})

const rows = computed<MicroCustomer[]>(() => customers.data?.customers || [])

// Picking customers to act on together. A Set survives repeated toggles
// cheaply; it is swapped rather than mutated in place so Vue's reactivity
// notices every change.
const selected = ref<Set<string>>(new Set())

function toggleSelected(name: string) {
  const next = new Set(selected.value)
  if (next.has(name)) next.delete(name)
  else next.add(name)
  selected.value = next
}

const allOnPageSelected = computed(
  () => rows.value.length > 0 && rows.value.every((c) => selected.value.has(c.name)),
)

function toggleSelectAll() {
  const next = new Set(selected.value)
  if (allOnPageSelected.value) {
    rows.value.forEach((c) => next.delete(c.name))
  } else {
    rows.value.forEach((c) => next.add(c.name))
  }
  selected.value = next
}

function clearSelection() {
  selected.value = new Set()
}

// Every narrowing is a server parameter: filtering the fetched page only would
// answer "3 Architekten" when the base holds 47.
const params = computed(() => ({
  limit_start: (page.value - 1) * pageSize,
  limit_page_length: pageSize,
  search: search.value || undefined,
  segment: segmentFilter.value || undefined,
  tag: tagFilter.value || undefined,
  source: sourceFilter.value || undefined,
  pipeline: pipelineFilter.value || undefined,
  pipeline_state: pipelineFilter.value ? pipelineState.value : undefined,
}))

watch(
  params,
  () => {
    customers.update({ params: params.value })
    customers.reload()
  },
  { deep: true },
)

// A narrowed audience always starts on page one. Whatever was checked belonged
// to the old list, so it does not carry over to the new one.
watch([segmentFilter, tagFilter, sourceFilter, pipelineFilter, pipelineState, search], () => {
  page.value = 1
  clearSelection()
})

watch(page, clearSelection)

const secondaryFilters = computed(
  () =>
    [tagFilter.value, sourceFilter.value, pipelineFilter.value].filter(Boolean).length,
)

const hasFilters = computed(() => Boolean(segmentFilter.value) || secondaryFilters.value > 0)

function clearFilters() {
  segmentFilter.value = ''
  tagFilter.value = ''
  sourceFilter.value = ''
  pipelineFilter.value = ''
}

const segmentChips = computed<CustomerFacets['segments']>(() => facets.data?.segments || [])

function segmentLabel(customer: MicroCustomer): string {
  const match = segmentChips.value.find((s) => s.name === customer.micro_segment)
  return match?.segment_name || customer.micro_segment || ''
}

function segmentColor(customer: MicroCustomer): string {
  const match = segmentChips.value.find((s) => s.name === customer.micro_segment)
  return segmentClasses[match?.color || 'Gray']
}

function tagsOf(customer: MicroCustomer): string[] {
  return (customer._user_tags || '').split(',').filter(Boolean)
}

const segmentClasses: Record<string, string> = {
  Gray: 'bg-gray-100 text-gray-700',
  Blue: 'bg-blue-100 text-blue-800',
  Green: 'bg-green-100 text-green-800',
  Yellow: 'bg-yellow-100 text-yellow-800',
  Orange: 'bg-orange-100 text-orange-800',
  Red: 'bg-red-100 text-red-800',
  Purple: 'bg-purple-100 text-purple-800',
  Pink: 'bg-pink-100 text-pink-800',
}

function openCustomer(name: string) {
  router.push(`/micro/customers/${name}`)
}

// Bulk delete: the same remove/erase split as a single customer's delete
// dialog, run over every checked row at once.
const bulkDeleteOpen = ref(false)
const bulkDeleting = ref('')
const bulkDeleteError = ref('')
const bulkDeleteResult = ref<BulkDeleteResult | null>(null)

const bulkDelete = createResource({
  url: 'micro.api.customers.bulk_delete_customers',
  onSuccess(data: BulkDeleteResult) {
    bulkDeleting.value = ''
    bulkDeleteResult.value = data
    customers.reload()
    facets.reload()
  },
  onError(err: { messages?: string[] }) {
    bulkDeleting.value = ''
    bulkDeleteError.value = err.messages?.[0] || __('Could not delete these customers')
  },
})

function openBulkDelete() {
  bulkDeleteError.value = ''
  bulkDeleteResult.value = null
  bulkDeleteOpen.value = true
}

function closeBulkDelete() {
  bulkDeleteOpen.value = false
  if (bulkDeleteResult.value) clearSelection()
}

function runBulkDelete(mode: 'remove' | 'erase') {
  bulkDeleteError.value = ''
  bulkDeleting.value = mode
  bulkDelete.submit({ customer_ids: Array.from(selected.value), mode })
}

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
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Customers') }}
      </h1>
      <router-link
        to="/micro/customers/new"
        class="rounded-md bg-accent-600 px-3 py-2 text-sm font-medium text-white hover:bg-accent-700"
      >
        {{ __('New Customer') }}
      </router-link>
    </div>

    <!-- Duplicates banner -->
    <router-link
      v-if="duplicates.data?.open"
      to="/micro/customers/duplicates"
      class="mb-4 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 hover:bg-amber-100"
    >
      <span class="text-sm font-medium text-amber-900">
        {{ duplicates.data.open }} {{ __('possible duplicates found') }}
      </span>
      <span class="text-sm font-medium text-amber-900 underline">{{ __('Review') }}</span>
    </router-link>

    <!-- Search -->
    <div class="mb-3 flex gap-3">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search customers...')"
        class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      />
      <button
        type="button"
        class="rounded-md border px-3 py-2 text-sm font-medium"
        :class="secondaryFilters ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
        @click="showFilters = !showFilters"
      >
        {{ __('Filters') }}<span v-if="secondaryFilters"> ({{ secondaryFilters }})</span>
      </button>
    </div>

    <!-- Segments: the categories themselves, with the size of each audience -->
    <div class="mb-3 flex flex-wrap items-center gap-2">
      <button
        type="button"
        class="rounded-full px-3 py-1 text-xs font-medium"
        :class="segmentFilter ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' : 'bg-gray-900 text-white'"
        @click="segmentFilter = ''"
      >
        {{ __('All') }}
        <span class="opacity-60">{{ facets.data?.total ?? '' }}</span>
      </button>
      <button
        v-for="segment in segmentChips"
        :key="segment.name"
        type="button"
        class="rounded-full px-3 py-1 text-xs font-medium"
        :class="[
          segmentClasses[segment.color || 'Gray'],
          segmentFilter === segment.name ? 'ring-2 ring-gray-900 ring-offset-1' : 'hover:opacity-80',
        ]"
        @click="segmentFilter = segmentFilter === segment.name ? '' : segment.name"
      >
        {{ segment.segment_name }}
        <span class="opacity-60">{{ segment.count }}</span>
      </button>
      <button
        v-if="facets.data?.unsegmented"
        type="button"
        class="rounded-full border border-dashed border-gray-300 px-3 py-1 text-xs font-medium text-gray-500"
        :class="segmentFilter === NO_SEGMENT ? 'ring-2 ring-gray-900 ring-offset-1' : 'hover:bg-gray-50'"
        @click="segmentFilter = segmentFilter === NO_SEGMENT ? '' : NO_SEGMENT"
      >
        {{ __('Uncategorised') }}
        <span class="opacity-60">{{ facets.data.unsegmented }}</span>
      </button>
      <a
        href="/app/micro-segment/new"
        class="rounded-full px-2 py-1 text-xs font-medium text-gray-400 hover:text-gray-700"
        :title="__('Create a category')"
      >
        + {{ __('Category') }}
      </a>
    </div>

    <!-- The rarer filters stay out of the way until they are asked for -->
    <div v-if="showFilters" class="mb-3 flex flex-wrap gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
      <select
        v-model="tagFilter"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      >
        <option value="">{{ __('All Tags') }}</option>
        <option v-for="t in facets.data?.tags || []" :key="t.tag" :value="t.tag">
          {{ t.tag }} ({{ t.count }})
        </option>
      </select>
      <select
        v-model="sourceFilter"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      >
        <option value="">{{ __('All Sources') }}</option>
        <option v-for="src in sources" :key="src" :value="src">
          {{ __(src) }}
        </option>
      </select>
      <select
        v-model="pipelineFilter"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      >
        <option value="">{{ __('All Pipelines') }}</option>
        <option v-for="p in pipelines.data?.pipelines || []" :key="p.name" :value="p.name">
          {{ p.pipeline_name }}
        </option>
      </select>
      <select
        v-if="pipelineFilter"
        v-model="pipelineState"
        class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      >
        <option v-for="state in pipelineStates" :key="state.value" :value="state.value">
          {{ __(state.label) }}
        </option>
      </select>
      <button
        v-if="hasFilters"
        type="button"
        class="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900"
        @click="clearFilters"
      >
        {{ __('Clear all') }}
      </button>
    </div>

    <!-- What the list is currently showing, in one line -->
    <p v-if="hasFilters" class="mb-3 text-sm text-gray-500">
      {{ customers.data?.total ?? 0 }} {{ __('of') }} {{ facets.data?.total ?? 0 }}
      {{ __('customers') }}
    </p>

    <!-- Bulk actions: appears once something is checked, gone otherwise -->
    <div
      v-if="selected.size"
      class="mb-3 flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-2"
    >
      <span class="text-sm font-medium text-gray-700">
        {{ selected.size }} {{ __('selected') }}
      </span>
      <div class="flex items-center gap-4">
        <button
          type="button"
          class="text-sm font-medium text-gray-600 hover:text-gray-900"
          @click="clearSelection"
        >
          {{ __('Clear selection') }}
        </button>
        <button
          type="button"
          class="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
          @click="openBulkDelete"
        >
          {{ __('Delete') }}
        </button>
      </div>
    </div>

    <!-- Customer list -->
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="w-10 px-4 py-3">
              <FieldLabel field="select_all_customers" :uppercase="false">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-gray-300"
                  :checked="allOnPageSelected"
                  @change="toggleSelectAll"
                />
              </FieldLabel>
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Name') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Category') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Status') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Type') }}
            </th>
            <th class="px-4 py-3 text-center text-xs font-medium uppercase text-gray-500">
              {{ __('Health Score') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Email') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Phone') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="customer in rows"
            :key="customer.name"
            class="cursor-pointer hover:bg-gray-50"
            @click="openCustomer(customer.name)"
          >
            <td class="px-4 py-3" @click.stop>
              <FieldLabel field="select_customer" :uppercase="false">
                <input
                  type="checkbox"
                  class="h-4 w-4 rounded border-gray-300"
                  :checked="selected.has(customer.name)"
                  @change="toggleSelected(customer.name)"
                />
              </FieldLabel>
            </td>
            <td class="px-4 py-3 text-sm font-medium text-gray-900">
              {{ customer.full_name }}
              <!-- Tags ride along under the name: many per contact, so they get
                   no column of their own -->
              <span
                v-for="tag in tagsOf(customer).slice(0, 3)"
                :key="tag"
                class="ml-1 inline-flex rounded bg-gray-100 px-1.5 py-0.5 text-xs font-normal text-gray-600"
              >
                {{ tag }}
              </span>
              <span v-if="tagsOf(customer).length > 3" class="ml-1 text-xs text-gray-400">
                +{{ tagsOf(customer).length - 3 }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm">
              <span
                v-if="customer.micro_segment"
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="segmentColor(customer)"
              >
                {{ segmentLabel(customer) }}
              </span>
              <span v-else class="text-xs text-gray-300">—</span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="statusClasses[customer.micro_status] || 'bg-gray-100 text-gray-600'"
              >
                {{ __(customer.micro_status) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="customer.micro_contact_type === 'Person' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'"
              >
                {{ __(customer.micro_contact_type) }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-center">
              <span
                v-if="customer.micro_health_score"
                class="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
                :class="gradeClasses[customer.micro_health_score] || 'bg-gray-100 text-gray-500'"
              >
                {{ customer.micro_health_score }}
              </span>
              <span v-else class="text-xs text-gray-300">—</span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ customer.email_id || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ customer.phone || '—' }}
            </td>
          </tr>

          <tr v-if="customers.loading">
            <td colspan="8" class="px-4 py-8 text-center text-sm text-gray-500">
              {{ __('Loading...') }}
            </td>
          </tr>

          <tr v-else-if="customers.error">
            <td colspan="8" class="px-4 py-8 text-center text-sm text-red-500">
              {{ __('Failed to load customers. Please try again.') }}
            </td>
          </tr>

          <tr v-else-if="!rows.length">
            <td colspan="8" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ search || hasFilters ? __('No customers match your search') : __('No customers yet') }}</p>
              <router-link
                v-if="!search && !hasFilters"
                to="/micro/customers/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Create your first customer') }} &rarr;
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="customers.data?.total && customers.data.total > pageSize"
      class="mt-4 flex items-center justify-between"
    >
      <button
        :disabled="page <= 1"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page--"
      >
        {{ __('Previous') }}
      </button>
      <span class="text-sm text-gray-500">
        {{ __('Page') }} {{ page }}
      </span>
      <button
        :disabled="page * pageSize >= customers.data.total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page++"
      >
        {{ __('Next') }}
      </button>
    </div>

    <!-- Bulk delete: same remove/erase split as a single customer's dialog -->
    <div
      v-if="bulkDeleteOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      @click.self="closeBulkDelete"
    >
      <div class="w-full max-w-lg rounded-xl bg-white p-5 shadow-xl">
        <h2 class="text-base font-semibold text-gray-900">
          {{ __('Delete') }} {{ selected.size }} {{ __('customers') }}
        </h2>

        <div v-if="bulkDeleteError" class="mt-4 rounded-md bg-red-50 p-3">
          <p class="text-sm text-red-700">{{ bulkDeleteError }}</p>
        </div>

        <!-- Result: what actually happened, once the request comes back -->
        <div v-if="bulkDeleteResult" class="mt-4 space-y-3">
          <p class="text-sm text-gray-700">
            {{ bulkDeleteResult.succeeded.length }}
            {{ bulkDeleteResult.mode === 'erase' ? __('customers erased') : __('customers removed from Micro') }}.
          </p>
          <div v-if="bulkDeleteResult.failed.length">
            <p class="text-sm text-gray-700">
              {{ bulkDeleteResult.failed.length }} {{ __('skipped:') }}
            </p>
            <ul class="mt-1 space-y-0.5 text-sm text-red-600">
              <li v-for="item in bulkDeleteResult.failed" :key="item.customer">
                · {{ item.error }}
              </li>
            </ul>
          </div>
          <div class="mt-5 flex justify-end">
            <button
              type="button"
              class="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700"
              @click="closeBulkDelete"
            >
              {{ __('Done') }}
            </button>
          </div>
        </div>

        <!-- Choice: remove or erase, before anything runs -->
        <div v-else class="mt-4 space-y-4">
          <div class="rounded-lg border border-gray-200 p-4">
            <p class="text-sm font-medium text-gray-900">{{ __('Remove from Micro') }}</p>
            <p class="mt-1 text-sm text-gray-500">
              {{ __('Stops being a customer and frees a slot under your limit. Every document stays, and the contacts remain available to your other apps. You can add them back later.') }}
            </p>
            <button
              type="button"
              :disabled="Boolean(bulkDeleting)"
              class="mt-3 rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
              @click="runBulkDelete('remove')"
            >
              {{ bulkDeleting === 'remove' ? __('Removing...') : __('Remove from Micro') }}
            </button>
          </div>

          <div class="rounded-lg border border-gray-200 p-4">
            <p class="text-sm font-medium text-gray-900">{{ __('Delete permanently') }}</p>
            <p class="mt-1 text-sm text-gray-500">
              {{ __('Erases the contact records themselves. This cannot be undone. Any customer with documents that have to be kept is skipped, and reported once the rest are done.') }}
            </p>
            <button
              type="button"
              :disabled="Boolean(bulkDeleting)"
              class="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              @click="runBulkDelete('erase')"
            >
              {{ bulkDeleting === 'erase' ? __('Deleting...') : __('Delete permanently') }}
            </button>
          </div>

          <div class="flex justify-end">
            <button
              type="button"
              class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              @click="closeBulkDelete"
            >
              {{ __('Cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
