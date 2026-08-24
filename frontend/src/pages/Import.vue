<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { computed, ref } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import { guessColumn, parseTable, type ParsedTable } from '@/utils/parseTable'
import type { ImportSetup, ImportResult, PipelinesListResponse } from '@/types/micro'

// Batched so a 3,000-row file never rides in one request, and so the user
// watches progress instead of a spinner.
const BATCH_SIZE = 100

const table = ref<ParsedTable | null>(null)
const fileName = ref('')
const parseError = ref('')
const mapping = ref<Record<string, string>>({})

const contactType = ref('Organization')
const status = ref('Potential')
const dedupeBy = ref('phone')
const onDuplicate = ref('skip')
const createLeads = ref(false)
const pipeline = ref('')

const running = ref(false)
const done = ref(false)
const processed = ref(0)
const totals = ref({ created: 0, updated: 0, skipped: 0, leads: 0, failed: 0, warned: 0 })
const failures = ref<{ row: number; error: string }[]>([])
const limitReached = ref(false)
const runError = ref('')

const setup = createResource({
  url: 'micro.api.imports.get_import_setup',
  auto: true,
  transform(data: ImportSetup) {
    return data
  },
})

const pipelines = createResource({
  url: 'micro.api.pipeline.get_pipelines',
  auto: true,
  transform(data: PipelinesListResponse) {
    return data
  },
  onSuccess(data: PipelinesListResponse) {
    if (!pipeline.value) pipeline.value = data.default || data.pipelines[0]?.name || ''
  },
})

const importContacts = createResource({ url: 'micro.api.imports.import_contacts' })

const capacity = computed(() => setup.data?.capacity)
const rowCount = computed(() => table.value?.rows.length || 0)
const previewRows = computed(() => table.value?.rows.slice(0, 5) || [])
const hasName = computed(() => Boolean(mapping.value.name))

const overCapacity = computed(() => {
  const remaining = capacity.value?.remaining
  return remaining !== null && remaining !== undefined && rowCount.value > remaining
})

const progress = computed(() =>
  rowCount.value ? Math.round((processed.value / rowCount.value) * 100) : 0,
)

function onFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  parseError.value = ''
  done.value = false
  fileName.value = file.name

  const reader = new FileReader()
  reader.onload = () => {
    try {
      const parsed = parseTable(String(reader.result), file.name)
      if (!parsed.rows.length) {
        parseError.value = __('No rows found in this file')
        table.value = null
        return
      }
      table.value = parsed
      autoMap(parsed)
    } catch (error) {
      table.value = null
      parseError.value = `${__('Could not read this file')}: ${String(error)}`
    }
  }
  reader.onerror = () => {
    parseError.value = __('Could not read this file')
  }
  reader.readAsText(file)
}

function autoMap(parsed: ParsedTable) {
  const next: Record<string, string> = {}
  for (const field of setup.data?.fields || []) {
    next[field.field] = guessColumn(parsed.columns, field.hints)
  }
  // Street and the composite address field both match "address"; prefer the
  // composite, since that is the shape scraped data usually arrives in.
  if (next.address_full && next.address === next.address_full) next.address = ''
  mapping.value = next
}

function resetRun() {
  processed.value = 0
  totals.value = { created: 0, updated: 0, skipped: 0, leads: 0, failed: 0, warned: 0 }
  failures.value = []
  limitReached.value = false
  runError.value = ''
  done.value = false
}

async function runImport() {
  if (!table.value || !hasName.value) return

  resetRun()
  running.value = true

  const rows = table.value.rows

  try {
    for (let start = 0; start < rows.length; start += BATCH_SIZE) {
      const batch = rows.slice(start, start + BATCH_SIZE)

      const result: ImportResult = await importContacts.submit({
        rows: JSON.stringify(batch),
        mapping: JSON.stringify(mapping.value),
        contact_type: contactType.value,
        status: status.value,
        dedupe_by: dedupeBy.value,
        on_duplicate: onDuplicate.value,
        create_leads: createLeads.value ? 1 : 0,
        pipeline: createLeads.value ? pipeline.value : undefined,
      })

      totals.value.created += result.created
      totals.value.updated += result.updated
      totals.value.skipped += result.skipped
      totals.value.leads += result.leads_created
      totals.value.failed += result.failed
      totals.value.warned += result.warned
      failures.value.push(
        ...result.failures.map((f) => ({ row: f.row + start + 1, error: f.error })),
      )
      processed.value = Math.min(start + batch.length, rows.length)

      if (result.limit_reached) {
        limitReached.value = true
        break
      }
    }
    done.value = true
    setup.reload()
  } catch (error) {
    runError.value =
      (error as { messages?: string[] })?.messages?.[0] || __('Import failed')
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="p-6">
    <h1 class="text-xl font-semibold text-gray-900">{{ __('Import Contacts') }}</h1>
    <p class="mt-1 text-sm text-gray-500">
      {{ __('Load contacts from a CSV or JSONL file. Financial documents are not imported.') }}
    </p>

    <!-- Capacity -->
    <div v-if="capacity" class="mt-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm">
      <span v-if="capacity.unlimited" class="text-gray-600">
        {{ __('No customer limit on this site.') }}
      </span>
      <span v-else class="text-gray-600">
        {{ capacity.used }} / {{ capacity.limit }} {{ __('customers used') }} &middot;
        <strong>{{ capacity.remaining }}</strong> {{ __('slots left') }}
      </span>
    </div>

    <!-- File -->
    <div class="mt-6">
      <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('File') }}</label>
      <input
        type="file"
        accept=".csv,.jsonl,.ndjson,.json,.txt"
        class="block w-full max-w-md text-sm text-gray-700 file:mr-3 file:rounded-md file:border-0 file:bg-gray-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-gray-800"
        @change="onFile"
      />
      <p v-if="parseError" class="mt-2 text-sm text-red-600">{{ parseError }}</p>
      <p v-else-if="table" class="mt-2 text-sm text-gray-600">
        {{ fileName }} &middot; {{ rowCount }} {{ __('rows') }} &middot;
        {{ table.format.toUpperCase() }}
        <span v-if="table.badLines.length" class="text-amber-600">
          &middot; {{ table.badLines.length }} {{ __('unreadable lines skipped') }}
        </span>
      </p>
    </div>

    <template v-if="table">
      <!-- Preview -->
      <div class="mt-6">
        <h2 class="mb-2 text-sm font-semibold text-gray-900">{{ __('Preview') }}</h2>
        <div class="overflow-x-auto rounded-lg border border-gray-200">
          <table class="min-w-full text-left text-xs">
            <thead class="bg-gray-50 text-gray-500">
              <tr>
                <th v-for="column in table.columns" :key="column" class="px-3 py-2 font-medium">
                  {{ column }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="(row, index) in previewRows" :key="index">
                <td
                  v-for="column in table.columns"
                  :key="column"
                  class="max-w-[220px] truncate px-3 py-2 text-gray-700"
                >
                  {{ row[column] }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Mapping -->
      <div class="mt-6">
        <h2 class="mb-2 text-sm font-semibold text-gray-900">{{ __('Map columns') }}</h2>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div v-for="field in setup.data?.fields || []" :key="field.field">
            <label class="mb-1 block text-xs font-medium text-gray-500">
              {{ __(field.label) }}
              <span v-if="field.field === 'name'" class="text-red-500">*</span>
            </label>
            <select
              v-model="mapping[field.field]"
              class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
            >
              <option value="">{{ __('Not imported') }}</option>
              <option v-for="column in table.columns" :key="column" :value="column">
                {{ column }}
              </option>
            </select>
          </div>
        </div>
        <p v-if="!hasName" class="mt-2 text-xs text-red-600">
          {{ __('Map a column to Name before importing.') }}
        </p>
      </div>

      <!-- Options -->
      <div class="mt-6">
        <h2 class="mb-2 text-sm font-semibold text-gray-900">{{ __('Options') }}</h2>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Contact Type') }}</label>
            <select
              v-model="contactType"
              class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
            >
              <option value="Organization">{{ __('Organization') }}</option>
              <option value="Person">{{ __('Person') }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">{{ __('Status') }}</label>
            <select
              v-model="status"
              class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
            >
              <option value="Potential">{{ __('Potential') }}</option>
              <option value="Active">{{ __('Active') }}</option>
              <option value="Inactive">{{ __('Inactive') }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">
              {{ __('Find duplicates by') }}
            </label>
            <select
              v-model="dedupeBy"
              class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
            >
              <option value="phone">{{ __('Phone') }}</option>
              <option value="email">{{ __('Email') }}</option>
              <option value="name">{{ __('Name') }}</option>
              <option value="none">{{ __('Do not check') }}</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-500">
              {{ __('On duplicate') }}
            </label>
            <select
              v-model="onDuplicate"
              class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
            >
              <option value="skip">{{ __('Skip') }}</option>
              <option value="update">{{ __('Fill in blanks') }}</option>
            </select>
          </div>
        </div>

        <label class="mt-3 flex cursor-pointer items-center gap-2 text-sm text-gray-600">
          <input
            v-model="createLeads"
            type="checkbox"
            class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
          />
          {{ __('Also create a lead for every row — new and existing contacts') }}
        </label>
        <select
          v-if="createLeads"
          v-model="pipeline"
          class="mt-2 w-full max-w-xs rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
        >
          <option v-for="p in pipelines.data?.pipelines || []" :key="p.name" :value="p.name">
            {{ p.pipeline_name }}
          </option>
        </select>
      </div>

      <!-- Capacity warning -->
      <p v-if="overCapacity" class="mt-4 text-sm text-amber-700">
        {{ __('This file has more rows than you have slots left. The import will stop when the limit is reached.') }}
      </p>

      <!-- Run -->
      <div class="mt-6 flex items-center gap-3">
        <button
          type="button"
          class="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
          :disabled="running || !hasName || (createLeads && !pipeline)"
          @click="runImport"
        >
          {{ running ? __('Importing...') : __('Import') }}
        </button>
        <span v-if="running || done" class="text-sm text-gray-600">
          {{ processed }} / {{ rowCount }} ({{ progress }}%)
        </span>
      </div>

      <div v-if="running || done" class="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-gray-100">
        <div class="h-full bg-gray-900 transition-all" :style="{ width: `${progress}%` }" />
      </div>

      <p v-if="runError" class="mt-3 text-sm text-red-600">{{ runError }}</p>

      <!-- Result -->
      <div v-if="done || running" class="mt-4 flex flex-wrap gap-4 text-sm">
        <span class="text-green-700">{{ totals.created }} {{ __('created') }}</span>
        <span class="text-blue-700">{{ totals.updated }} {{ __('updated') }}</span>
        <span class="text-gray-600">{{ totals.skipped }} {{ __('skipped as duplicates') }}</span>
        <span v-if="createLeads" class="text-gray-700">
          {{ totals.leads }} {{ __('leads added') }}
        </span>
        <span v-if="totals.failed" class="text-red-700">
          {{ totals.failed }} {{ __('failed') }}
        </span>
        <span v-if="totals.warned" class="text-amber-700">
          {{ totals.warned }} {{ __('fields left empty (too long)') }}
        </span>
      </div>

      <p v-if="limitReached" class="mt-3 text-sm text-amber-700">
        {{ __('Stopped: the customer limit was reached.') }}
      </p>

      <div v-if="failures.length" class="mt-4">
        <h3 class="mb-1 text-xs font-semibold text-gray-700">{{ __('Rows that failed') }}</h3>
        <ul class="max-h-48 overflow-auto rounded-md border border-gray-200 text-xs">
          <li
            v-for="failure in failures.slice(0, 100)"
            :key="`${failure.row}-${failure.error}`"
            class="border-b border-gray-100 px-3 py-1.5 text-gray-600 last:border-0"
          >
            {{ __('Row') }} {{ failure.row }}: {{ failure.error }}
          </li>
        </ul>
      </div>

      <div v-if="done && totals.created" class="mt-4">
        <router-link to="/micro/customers" class="text-sm font-medium text-accent-600 hover:underline">
          {{ __('View contacts') }} &rarr;
        </router-link>
      </div>
    </template>
  </div>
</template>
