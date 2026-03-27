<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const docType = ref('Micro Receipt')
const fromDate = ref('')
const toDate = ref('')
const category = ref('')
const onlyUnexported = ref(false)
const markExported = ref(false)
const exporting = ref(false)
const exportResult = ref<{ count: number; filename: string } | null>(null)

const categories = ['', 'Materials', 'Travel', 'Office', 'Food', 'Software', 'Services', 'Other']

const preview = createResource({
  url: 'micro.api.export.get_export_preview',
  params: {
    doc_type: docType.value,
    from_date: fromDate.value || undefined,
    to_date: toDate.value || undefined,
    category: category.value || undefined,
    only_unexported: onlyUnexported.value ? 1 : 0,
  },
  auto: true,
})

watch([docType, fromDate, toDate, category, onlyUnexported], () => {
  exportResult.value = null
  preview.update({
    params: {
      doc_type: docType.value,
      from_date: fromDate.value || undefined,
      to_date: toDate.value || undefined,
      category: docType.value === 'Micro Receipt' ? (category.value || undefined) : undefined,
      only_unexported: onlyUnexported.value ? 1 : 0,
    },
  })
  preview.reload()
})

const exportResource = createResource({
  url: 'micro.api.export.export_csv',
})

async function doExport() {
  exporting.value = true
  exportResult.value = null
  try {
    await exportResource.update({
      params: {
        doc_type: docType.value,
        from_date: fromDate.value || undefined,
        to_date: toDate.value || undefined,
        category: docType.value === 'Micro Receipt' ? (category.value || undefined) : undefined,
        only_unexported: onlyUnexported.value ? 1 : 0,
        mark_exported: markExported.value ? 1 : 0,
      },
    })
    await exportResource.reload()

    if (exportResource.data?.csv) {
      const blob = new Blob([exportResource.data.csv], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = exportResource.data.filename
      link.click()
      URL.revokeObjectURL(url)

      exportResult.value = {
        count: exportResource.data.count,
        filename: exportResource.data.filename,
      }

      // Refresh preview after marking exported
      if (markExported.value) {
        preview.reload()
      }
    }
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold text-gray-900">
      {{ __('Export to Tax Advisor') }}
    </h1>

    <div class="space-y-6">
      <!-- Document Type -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Document Type') }}
        </h2>
        <div class="flex gap-3">
          <label
            class="flex cursor-pointer items-center gap-2 rounded-md border px-4 py-2 text-sm"
            :class="docType === 'Micro Receipt'
              ? 'border-accent-600 bg-accent-600 text-white'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
          >
            <input v-model="docType" type="radio" value="Micro Receipt" class="sr-only" />
            {{ __('Receipts') }}
          </label>
          <label
            class="flex cursor-pointer items-center gap-2 rounded-md border px-4 py-2 text-sm"
            :class="docType === 'Micro Invoice Draft'
              ? 'border-accent-600 bg-accent-600 text-white'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50'"
          >
            <input v-model="docType" type="radio" value="Micro Invoice Draft" class="sr-only" />
            {{ __('Invoice Drafts') }}
          </label>
        </div>
      </div>

      <!-- Filters -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Filters') }}
        </h2>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs text-gray-500">{{ __('From Date') }}</label>
            <input
              v-model="fromDate"
              type="date"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
          <div>
            <label class="mb-1 block text-xs text-gray-500">{{ __('To Date') }}</label>
            <input
              v-model="toDate"
              type="date"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500 dark:focus:ring-accent-400"
            />
          </div>
        </div>

        <!-- Receipt-specific filters -->
        <div v-if="docType === 'Micro Receipt'" class="mt-4 grid grid-cols-2 gap-4">
          <div>
            <label class="mb-1 block text-xs text-gray-500">{{ __('Category') }}</label>
            <select
              v-model="category"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-accent-500 focus:outline-none focus:ring-1 focus:ring-accent-500 dark:focus:ring-accent-400"
            >
              <option value="">{{ __('All Categories') }}</option>
              <option v-for="cat in categories.slice(1)" :key="cat" :value="cat">
                {{ __(cat) }}
              </option>
            </select>
          </div>
          <div class="flex items-end">
            <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
              <input
                v-model="onlyUnexported"
                type="checkbox"
                class="rounded border-gray-300 accent-accent-600 focus:ring-accent-500"
              />
              {{ __('Only unexported') }}
            </label>
          </div>
        </div>
      </div>

      <!-- Preview -->
      <div class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
        <h2 class="mb-4 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {{ __('Preview') }}
        </h2>
        <div class="flex items-center justify-between">
          <div>
            <span class="text-3xl font-bold text-gray-900">
              {{ preview.data?.count ?? '—' }}
            </span>
            <span class="ml-2 text-sm text-gray-500">
              {{ __('documents to export') }}
            </span>
          </div>
        </div>

        <!-- Mark exported option (receipts only) -->
        <div v-if="docType === 'Micro Receipt'" class="mt-4">
          <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
            <input
              v-model="markExported"
              type="checkbox"
              class="rounded border-gray-300 accent-accent-600 focus:ring-accent-500"
            />
            {{ __('Mark as exported after download') }}
          </label>
        </div>
      </div>

      <!-- Export Button -->
      <div class="flex items-center gap-4">
        <button
          :disabled="!preview.data?.count || exporting"
          class="rounded-md bg-accent-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
          @click="doExport"
        >
          {{ exporting ? __('Exporting...') : __('Download CSV') }}
        </button>

        <!-- Success message -->
        <div v-if="exportResult" class="text-sm text-green-600">
          {{ __('Exported {0} documents').replace('{0}', String(exportResult.count)) }}
        </div>
      </div>
    </div>
  </div>
</template>
