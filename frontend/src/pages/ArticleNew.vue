<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CategoryPicker from '@/components/CategoryPicker.vue'

const router = useRouter()

const form = ref({
  article_name: '',
  article_code: '',
  barcode: '',
  category: '',
  unit: 'Stück',
  is_active: true,
  selling_price: 0,
  purchase_price: 0,
  description: '',
  supplier: '',
  notes: '',
})

const error = ref('')
const submitting = ref(false)

const isValid = computed(() => {
  return form.value.article_name.trim().length > 0 && form.value.selling_price >= 0
})

const units = [
  { value: 'Stück', label: __('Piece') },
  { value: 'Stunde', label: __('Hour') },
  { value: 'Pauschal', label: __('Flat Rate') },
  { value: 'kg', label: 'kg' },
  { value: 'm', label: 'm' },
  { value: 'm²', label: 'm²' },
  { value: 'Liter', label: __('Liter') },
]

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

const createArticle = createResource({
  url: 'micro.api.articles.create_article',
  onSuccess(data: { article: { name: string } }) {
    router.push(`/micro/articles/${data.article.name}`)
  },
  onError(err: { messages?: string[] }) {
    submitting.value = false
    error.value = err.messages?.[0] || __('Failed to create article')
  },
})

function submit() {
  if (!form.value.article_name.trim()) {
    error.value = __('Article name is required')
    return
  }

  error.value = ''
  submitting.value = true

  const params: Record<string, unknown> = {
    article_name: form.value.article_name.trim(),
    selling_price: form.value.selling_price,
    unit: form.value.unit,
    is_active: form.value.is_active,
    purchase_price: form.value.purchase_price,
  }

  if (form.value.article_code.trim()) params.article_code = form.value.article_code.trim()
  if (form.value.barcode.trim()) params.barcode = form.value.barcode.trim()
  if (form.value.category) params.category = form.value.category
  if (form.value.description.trim()) params.description = form.value.description.trim()
  if (form.value.supplier.trim()) params.supplier = form.value.supplier.trim()
  if (form.value.notes.trim()) params.notes = form.value.notes.trim()

  createArticle.submit(params)
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3">
        <router-link to="/micro/articles" class="text-sm text-gray-500 hover:text-gray-700">
          {{ __('Articles') }}
        </router-link>
        <span class="text-gray-300">/</span>
        <span class="text-sm text-gray-700">{{ __('New Article') }}</span>
      </div>

      <div class="mt-2 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">{{ __('New Article') }}</h1>
        <div class="flex items-center gap-3">
          <router-link
            to="/micro/articles"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {{ __('Cancel') }}
          </router-link>
          <button
            :disabled="!isValid || submitting"
            class="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
            @click="submit"
          >
            {{ submitting ? __('Saving...') : __('Create Article') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 rounded-md bg-red-50 p-3">
      <p class="text-sm text-red-700">{{ error }}</p>
    </div>

    <!-- Form -->
    <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
      <!-- Details -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Details') }}</h3>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Article Name') }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.article_name"
              type="text"
              :placeholder="__('Article Name')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Article Code') }}</label>
              <input
                v-model="form.article_code"
                type="text"
                :placeholder="__('SKU')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Barcode / EAN') }}</label>
              <input
                v-model="form.barcode"
                type="text"
                :placeholder="__('EAN / UPC')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Category') }}</label>
            <CategoryPicker v-model="form.category" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Unit') }}</label>
              <select
                v-model="form.unit"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              >
                <option v-for="u in units" :key="u.value" :value="u.value">{{ u.label }}</option>
              </select>
            </div>
            <div class="flex items-end pb-2">
              <div class="flex items-center gap-2">
                <input id="is_active" v-model="form.is_active" type="checkbox" class="rounded border-gray-300" />
                <label for="is_active" class="text-sm font-medium text-gray-700">{{ __('Active') }}</label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pricing + Supplier -->
      <div class="space-y-6">
        <div class="rounded-lg border border-gray-200 bg-white p-5">
          <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Pricing') }}</h3>
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">
                  {{ __('Selling Price (VK)') }} <span class="text-red-500">*</span>
                </label>
                <input
                  v-model.number="form.selling_price"
                  type="number"
                  min="0"
                  step="0.01"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Purchase Price (EK)') }}</label>
                <input
                  v-model.number="form.purchase_price"
                  type="number"
                  min="0"
                  step="0.01"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                />
              </div>
            </div>
            <div v-if="form.selling_price > 0 && form.purchase_price > 0" class="rounded-md bg-gray-50 p-3">
              <p class="text-xs text-gray-500">{{ __('Margin') }}: {{ formatCurrency(form.selling_price - form.purchase_price) }}
                ({{ Math.round(((form.selling_price - form.purchase_price) / form.selling_price) * 100) }}%)
              </p>
            </div>
          </div>
        </div>

        <div class="rounded-lg border border-gray-200 bg-white p-5">
          <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Supplier & Notes') }}</h3>
          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Supplier') }}</label>
              <input
                v-model="form.supplier"
                type="text"
                :placeholder="__('Supplier')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Notes') }}</label>
              <textarea
                v-model="form.notes"
                rows="3"
                :placeholder="__('Internal notes...')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              ></textarea>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Description (full width) -->
    <div class="mt-6 rounded-lg border border-gray-200 bg-white p-5">
      <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Description') }}</h3>
      <textarea
        v-model="form.description"
        rows="4"
        :placeholder="__('Article description...')"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      ></textarea>
    </div>
  </div>
</template>
