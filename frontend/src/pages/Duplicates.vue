<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { DuplicatePair } from '@/types/micro'

const page = ref(1)
const pageSize = 20
const band = ref('')
const busy = ref('')
const error = ref('')

// Which of the two records survives, per pair. Defaults to whichever carries
// more history — the merge keeps both records' values either way, but the
// survivor's name is the one the contact keeps.
const keep = reactive<Record<string, string>>({})

const pairs = createResource({
  url: 'micro.api.duplicates.get_duplicate_pairs',
  params: { limit_start: 0, limit_page_length: pageSize },
  auto: true,
  transform(data: { pairs: DuplicatePair[]; total: number }) {
    for (const pair of data.pairs) {
      if (!keep[pair.name]) {
        keep[pair.name] =
          pair.documents_b.total > pair.documents_a.total ? pair.contact_b.name : pair.contact_a.name
      }
    }
    return data
  },
})

function reload() {
  pairs.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      band: band.value || undefined,
    },
  })
  pairs.reload()
}

function setBand(value: string) {
  band.value = value
  page.value = 1
  reload()
}

function goToPage(value: number) {
  page.value = value
  reload()
}

const scan = createResource({
  url: 'micro.api.duplicates.scan_for_duplicates',
  onSuccess() {
    busy.value = ''
    goToPage(1)
  },
  onError(err: { messages?: string[] }) {
    busy.value = ''
    error.value = err.messages?.[0] || __('Scan failed')
  },
})

const merge = createResource({
  url: 'micro.api.duplicates.merge_contacts',
  onSuccess() {
    busy.value = ''
    reload()
  },
  onError(err: { messages?: string[] }) {
    busy.value = ''
    error.value = err.messages?.[0] || __('Merge failed')
  },
})

const dismiss = createResource({
  url: 'micro.api.duplicates.dismiss_pair',
  onSuccess() {
    busy.value = ''
    reload()
  },
  onError(err: { messages?: string[] }) {
    busy.value = ''
    error.value = err.messages?.[0] || __('Could not dismiss this suggestion')
  },
})

function loserOf(pair: DuplicatePair): string {
  return keep[pair.name] === pair.contact_a.name ? pair.contact_b.name : pair.contact_a.name
}

function issuedFor(pair: DuplicatePair): number {
  const documents = loserOf(pair) === pair.contact_a.name ? pair.documents_a : pair.documents_b
  return documents.issued || 0
}

function runMerge(pair: DuplicatePair) {
  error.value = ''
  busy.value = pair.name
  merge.submit({ winner: keep[pair.name], loser: loserOf(pair), pair: pair.name })
}

function runDismiss(pair: DuplicatePair) {
  error.value = ''
  busy.value = pair.name
  dismiss.submit({ pair: pair.name })
}

function runScan() {
  error.value = ''
  busy.value = 'scan'
  scan.submit({})
}

const bandClasses: Record<string, string> = {
  Certain: 'bg-red-100 text-red-800',
  Likely: 'bg-amber-100 text-amber-800',
  Possible: 'bg-gray-100 text-gray-600',
}

const total = computed(() => pairs.data?.total || 0)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3">
        <router-link to="/micro/customers" class="text-sm text-gray-500 hover:text-gray-700">
          {{ __('Customers') }}
        </router-link>
        <span class="text-gray-300">/</span>
        <span class="text-sm text-gray-700">{{ __('Duplicates') }}</span>
      </div>

      <div class="mt-2 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">{{ __('Possible Duplicates') }}</h1>
        <button
          :disabled="busy === 'scan'"
          class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          @click="runScan"
        >
          {{ busy === 'scan' ? __('Scanning...') : __('Scan now') }}
        </button>
      </div>

      <p class="mt-1 text-sm text-gray-500">
        {{ __('Micro suggests, you decide. Nothing is merged automatically.') }}
      </p>
    </div>

    <div v-if="error" class="mb-4 rounded-md bg-red-50 p-3">
      <p class="text-sm text-red-700">{{ error }}</p>
    </div>

    <!-- Band filter -->
    <div class="mb-4 flex gap-2">
      <button
        v-for="option in ['', 'Certain', 'Likely', 'Possible']"
        :key="option || 'all'"
        class="rounded-md border px-3 py-1 text-sm"
        :class="band === option ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
        @click="setBand(option)"
      >
        {{ option ? __(option) : __('All') }}
      </button>
    </div>

    <!-- Loading / empty -->
    <div v-if="pairs.loading" class="rounded-lg border border-gray-200 bg-white p-8 text-center">
      <p class="text-sm text-gray-500">{{ __('Loading...') }}</p>
    </div>

    <div
      v-else-if="!pairs.data?.pairs?.length"
      class="rounded-lg border border-gray-200 bg-white p-12 text-center"
    >
      <p class="text-sm text-gray-500">{{ __('No duplicates found') }}</p>
      <p class="mt-1 text-xs text-gray-400">
        {{ __('Micro re-checks your contacts once a day.') }}
      </p>
    </div>

    <!-- Pair cards -->
    <div v-else class="space-y-4">
      <div
        v-for="pair in pairs.data.pairs"
        :key="pair.name"
        class="rounded-lg border border-gray-200 bg-white p-5"
      >
        <div class="mb-4 flex flex-wrap items-center gap-2">
          <span
            class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
            :class="bandClasses[pair.band] || 'bg-gray-100 text-gray-600'"
          >
            {{ __(pair.band) }}
          </span>
          <span class="text-xs text-gray-500">{{ Math.round(pair.score * 100) }}% {{ __('match') }}</span>
          <span class="text-gray-300">·</span>
          <span class="text-xs text-gray-500">{{ pair.reasons.join(' · ') }}</span>
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label
            v-for="side in [pair.contact_a, pair.contact_b]"
            :key="side.name"
            class="cursor-pointer rounded-md border p-4"
            :class="keep[pair.name] === side.name ? 'border-accent-600 bg-accent-50' : 'border-gray-200 hover:bg-gray-50'"
          >
            <div class="mb-2 flex items-center gap-2">
              <input
                v-model="keep[pair.name]"
                type="radio"
                :value="side.name"
                :name="`keep-${pair.name}`"
                class="text-accent-600"
              />
              <span class="text-sm font-medium text-gray-900">
                {{ keep[pair.name] === side.name ? __('Keep this one') : __('Merge into the other') }}
              </span>
            </div>

            <p class="text-sm font-medium text-gray-900">{{ side.full_name || side.name }}</p>
            <dl class="mt-2 space-y-1 text-sm text-gray-500">
              <div>{{ side.email_id || '—' }}</div>
              <div>{{ side.phone || side.mobile_no || '—' }}</div>
              <div v-if="side.micro_postal_code || side.micro_address">
                {{ [side.micro_address, side.micro_postal_code].filter(Boolean).join(', ') }}
              </div>
              <div class="text-xs text-gray-400">
                {{
                  (side.name === pair.contact_a.name ? pair.documents_a.total : pair.documents_b.total) || 0
                }}
                {{ __('linked documents') }}
                <span v-if="!side.micro_status">· {{ __('not a Micro customer') }}</span>
              </div>
            </dl>

            <router-link
              :to="`/micro/customers/${side.name}`"
              class="mt-2 inline-block text-xs text-gray-500 underline hover:text-gray-700"
              @click.stop
            >
              {{ __('Open') }}
            </router-link>
          </label>
        </div>

        <!-- Merging repoints documents that have already gone out. Saying so
             beats discovering it on the next reprint. -->
        <p v-if="issuedFor(pair)" class="mt-3 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
          {{ issuedFor(pair) }}
          {{ __('sent document(s) will point to the surviving contact after the merge.') }}
        </p>

        <div class="mt-4 flex items-center gap-3">
          <button
            :disabled="busy === pair.name"
            class="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
            @click="runMerge(pair)"
          >
            {{ busy === pair.name ? __('Merging...') : __('Merge') }}
          </button>
          <button
            :disabled="busy === pair.name"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            @click="runDismiss(pair)"
          >
            {{ __('Not a duplicate') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="mt-4 flex items-center justify-between">
      <button
        :disabled="page <= 1"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="goToPage(page - 1)"
      >
        {{ __('Previous') }}
      </button>
      <span class="text-sm text-gray-500">{{ __('Page') }} {{ page }}</span>
      <button
        :disabled="page * pageSize >= total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="goToPage(page + 1)"
      >
        {{ __('Next') }}
      </button>
    </div>
  </div>
</template>
