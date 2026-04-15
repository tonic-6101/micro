<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CategoryPicker from '@/components/CategoryPicker.vue'
import type { MicroArticle } from '@/types/micro'

const props = defineProps<{
  id: string
}>()

const editing = ref(false)
const saving = ref(false)
const error = ref('')

const editForm = ref({
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

const unitMap: Record<string, string> = {
  'Stück': __('Piece'),
  'Stunde': __('Hour'),
  'Pauschal': __('Flat Rate'),
  'kg': 'kg',
  'm': 'm',
  'm²': 'm²',
  'Liter': __('Liter'),
}

const units = Object.entries(unitMap).map(([value, label]) => ({ value, label }))

const article = createResource({
  url: 'micro.api.articles.get_article',
  params: { article_id: props.id },
  auto: true,
  transform(data: { article: MicroArticle }) {
    return data.article
  },
})

const isEditValid = computed(() => {
  return editForm.value.article_name.trim().length > 0 && editForm.value.selling_price >= 0
})

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

function startEditing() {
  if (!article.data) return

  editForm.value = {
    article_name: article.data.article_name || '',
    article_code: article.data.article_code || '',
    barcode: article.data.barcode || '',
    category: article.data.category || '',
    unit: article.data.unit || 'Stück',
    is_active: !!article.data.is_active,
    selling_price: article.data.selling_price || 0,
    purchase_price: article.data.purchase_price || 0,
    description: article.data.description || '',
    supplier: article.data.supplier || '',
    notes: article.data.notes || '',
  }
  error.value = ''
  editing.value = true
}

function cancelEditing() {
  editing.value = false
  error.value = ''
}

const updateArticle = createResource({
  url: 'micro.api.articles.update_article',
  onSuccess() {
    saving.value = false
    editing.value = false
    article.reload()
  },
  onError(err: { messages?: string[] }) {
    saving.value = false
    error.value = err.messages?.[0] || __('Failed to save article')
  },
})

function saveEdit() {
  if (!isEditValid.value) return
  error.value = ''
  saving.value = true

  updateArticle.submit({
    article_id: props.id,
    article_name: editForm.value.article_name.trim(),
    article_code: editForm.value.article_code.trim(),
    barcode: editForm.value.barcode.trim(),
    category: editForm.value.category,
    unit: editForm.value.unit,
    is_active: editForm.value.is_active,
    selling_price: editForm.value.selling_price,
    purchase_price: editForm.value.purchase_price,
    description: editForm.value.description,
    supplier: editForm.value.supplier.trim(),
    notes: editForm.value.notes,
  })
}
</script>

<template>
  <div v-if="article.loading" class="py-12 text-center text-sm text-gray-500">
    {{ __('Loading...') }}
  </div>

  <div v-else-if="article.error" class="py-12 text-center">
    <p class="text-sm text-red-500">{{ __('Failed to load article') }}</p>
    <router-link to="/micro/articles" class="mt-2 inline-block text-sm text-gray-500 hover:text-gray-700">
      &larr; {{ __('Back to Articles') }}
    </router-link>
  </div>

  <div v-else-if="article.data">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3">
        <router-link to="/micro/articles" class="text-sm text-gray-500 hover:text-gray-700">
          {{ __('Articles') }}
        </router-link>
        <span class="text-gray-300">/</span>
      </div>

      <div class="mt-2 flex items-start justify-between">
        <div class="flex items-center gap-4">
          <img
            v-if="article.data.image"
            :src="article.data.image"
            :alt="article.data.article_name"
            class="h-14 w-14 rounded-lg border border-gray-200 object-cover"
          />
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ article.data.article_name }}</h1>
            <p class="mt-1 text-sm text-gray-500">{{ article.data.name }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span
            class="inline-flex rounded-full px-3 py-1 text-sm font-medium"
            :class="article.data.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'"
          >
            {{ article.data.is_active ? __('Active') : __('Inactive') }}
          </span>
          <template v-if="!editing">
            <button
              class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              @click="startEditing"
            >
              {{ __('Edit') }}
            </button>
          </template>
          <template v-else>
            <button
              class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              @click="cancelEditing"
            >
              {{ __('Cancel') }}
            </button>
            <button
              :disabled="!isEditValid || saving"
              class="rounded-md bg-accent-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
              @click="saveEdit"
            >
              {{ saving ? __('Saving...') : __('Save') }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 rounded-md bg-red-50 p-3">
      <p class="text-sm text-red-700">{{ error }}</p>
    </div>

    <!-- ═══════════════════ VIEW MODE ═══════════════════ -->
    <template v-if="!editing">
      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <!-- Details -->
        <div class="rounded-lg border border-gray-200 bg-white p-5">
          <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Details') }}</h3>
          <dl class="space-y-3">
            <div>
              <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Article Name') }}</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ article.data.article_name }}</dd>
            </div>
            <div v-if="article.data.article_code">
              <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Article Code') }}</dt>
              <dd class="mt-1 font-mono text-sm text-gray-900">{{ article.data.article_code }}</dd>
            </div>
            <div v-if="article.data.barcode">
              <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Barcode / EAN') }}</dt>
              <dd class="mt-1 font-mono text-sm text-gray-900">{{ article.data.barcode }}</dd>
            </div>
            <div v-if="article.data.category">
              <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Category') }}</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ article.data.category }}</dd>
            </div>
            <div>
              <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Unit') }}</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ unitMap[article.data.unit || ''] || article.data.unit || '—' }}</dd>
            </div>
          </dl>
        </div>

        <!-- Pricing + Supplier -->
        <div class="space-y-6">
          <div class="rounded-lg border border-gray-200 bg-white p-5">
            <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Pricing') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <div class="text-xs font-medium uppercase text-gray-500">{{ __('Selling Price (VK)') }}</div>
                <div class="mt-1 text-lg font-bold text-gray-900">{{ formatCurrency(article.data.selling_price) }}</div>
              </div>
              <div>
                <div class="text-xs font-medium uppercase text-gray-500">{{ __('Purchase Price (EK)') }}</div>
                <div class="mt-1 text-lg text-gray-700">{{ formatCurrency(article.data.purchase_price) }}</div>
              </div>
            </div>
            <div v-if="article.data.selling_price > 0 && article.data.purchase_price > 0" class="mt-3 rounded-md bg-gray-50 p-3">
              <p class="text-xs text-gray-500">{{ __('Margin') }}: {{ formatCurrency(article.data.selling_price - article.data.purchase_price) }}
                ({{ Math.round(((article.data.selling_price - article.data.purchase_price) / article.data.selling_price) * 100) }}%)
              </p>
            </div>
          </div>

          <div v-if="article.data.supplier || article.data.notes" class="rounded-lg border border-gray-200 bg-white p-5">
            <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Supplier & Notes') }}</h3>
            <dl class="space-y-3">
              <div v-if="article.data.supplier">
                <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Supplier') }}</dt>
                <dd class="mt-1 text-sm text-gray-900">{{ article.data.supplier }}</dd>
              </div>
              <div v-if="article.data.notes">
                <dt class="text-xs font-medium uppercase text-gray-500">{{ __('Notes') }}</dt>
                <dd class="mt-1 text-sm text-gray-600">{{ article.data.notes }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <!-- Image -->
      <div v-if="article.data.image" class="mt-6 rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-3 text-sm font-medium uppercase text-gray-500">{{ __('Image') }}</h3>
        <img
          :src="article.data.image"
          :alt="article.data.article_name"
          class="max-h-64 rounded-lg border border-gray-200 object-contain"
        />
      </div>

      <!-- Description -->
      <div v-if="article.data.description" class="mt-6 rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-2 text-sm font-medium uppercase text-gray-500">{{ __('Description') }}</h3>
        <p class="text-sm text-gray-600">{{ article.data.description }}</p>
      </div>
    </template>

    <!-- ═══════════════════ EDIT MODE ═══════════════════ -->
    <template v-else>
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
                v-model="editForm.article_name"
                type="text"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Article Code') }}</label>
                <input
                  v-model="editForm.article_code"
                  type="text"
                  :placeholder="__('SKU')"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Barcode / EAN') }}</label>
                <input
                  v-model="editForm.barcode"
                  type="text"
                  :placeholder="__('EAN / UPC')"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                />
              </div>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Category') }}</label>
              <CategoryPicker v-model="editForm.category" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Unit') }}</label>
                <select
                  v-model="editForm.unit"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                >
                  <option v-for="u in units" :key="u.value" :value="u.value">{{ u.label }}</option>
                </select>
              </div>
              <div class="flex items-end pb-2">
                <div class="flex items-center gap-2">
                  <input id="edit_is_active" v-model="editForm.is_active" type="checkbox" class="rounded border-gray-300" />
                  <label for="edit_is_active" class="text-sm font-medium text-gray-700">{{ __('Active') }}</label>
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
                    v-model.number="editForm.selling_price"
                    type="number"
                    min="0"
                    step="0.01"
                    class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                  />
                </div>
                <div>
                  <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Purchase Price (EK)') }}</label>
                  <input
                    v-model.number="editForm.purchase_price"
                    type="number"
                    min="0"
                    step="0.01"
                    class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                  />
                </div>
              </div>
              <div v-if="editForm.selling_price > 0 && editForm.purchase_price > 0" class="rounded-md bg-gray-50 p-3">
                <p class="text-xs text-gray-500">{{ __('Margin') }}: {{ formatCurrency(editForm.selling_price - editForm.purchase_price) }}
                  ({{ Math.round(((editForm.selling_price - editForm.purchase_price) / editForm.selling_price) * 100) }}%)
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
                  v-model="editForm.supplier"
                  type="text"
                  :placeholder="__('Supplier')"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Notes') }}</label>
                <textarea
                  v-model="editForm.notes"
                  rows="3"
                  :placeholder="__('Internal notes...')"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Description -->
      <div class="mt-6 rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Description') }}</h3>
        <textarea
          v-model="editForm.description"
          rows="4"
          :placeholder="__('Article description...')"
          class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
        ></textarea>
      </div>
    </template>
  </div>
</template>
