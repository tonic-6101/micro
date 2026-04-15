<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroArticleCategory } from '@/types/micro'

const model = defineModel<string>({ default: '' })

const search = ref('')
const showDropdown = ref(false)
const creating = ref(false)

const categories = createResource({
  url: 'micro.api.articles.get_categories',
  auto: true,
  transform(data: { categories: MicroArticleCategory[] }) {
    return data.categories
  },
})

const filtered = computed(() => {
  if (!categories.data) return []
  if (!search.value.trim()) return categories.data
  const q = search.value.toLowerCase()
  return categories.data.filter((c: MicroArticleCategory) =>
    c.category_name.toLowerCase().includes(q),
  )
})

const canCreate = computed(() => {
  if (!search.value.trim()) return false
  if (!categories.data) return true
  return !categories.data.some(
    (c: MicroArticleCategory) => c.category_name.toLowerCase() === search.value.trim().toLowerCase(),
  )
})

const selectedLabel = computed(() => {
  if (!model.value || !categories.data) return ''
  const found = categories.data.find((c: MicroArticleCategory) => c.name === model.value)
  return found ? found.category_name : model.value
})

const createCategory = createResource({
  url: 'micro.api.articles.create_category',
  onSuccess(data: { category: { name: string } }) {
    creating.value = false
    model.value = data.category.name
    search.value = ''
    showDropdown.value = false
    categories.reload()
  },
  onError() {
    creating.value = false
  },
})

function selectCategory(name: string) {
  model.value = name
  search.value = ''
  showDropdown.value = false
}

function clearCategory() {
  model.value = ''
  search.value = ''
}

function createNew() {
  if (!search.value.trim() || creating.value) return
  creating.value = true
  createCategory.submit({ category_name: search.value.trim() })
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
        class="flex-1 cursor-pointer rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
        @click="onFocus"
      >
        {{ selectedLabel }}
      </div>
      <button
        class="text-gray-400 hover:text-gray-600"
        :title="__('Clear')"
        @click="clearCategory"
      >
        &times;
      </button>
    </div>

    <!-- Search input -->
    <input
      v-else
      v-model="search"
      type="text"
      :placeholder="__('Search or create category...')"
      class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      @focus="onFocus"
      @blur="onBlur"
    />

    <!-- Dropdown -->
    <div
      v-if="showDropdown"
      class="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md border border-gray-200 bg-white shadow-lg"
    >
      <div
        v-for="cat in filtered"
        :key="cat.name"
        class="cursor-pointer px-3 py-2 text-sm text-gray-900 hover:bg-gray-50"
        @mousedown.prevent="selectCategory(cat.name)"
      >
        {{ cat.category_name }}
      </div>

      <div v-if="!filtered.length && !canCreate" class="px-3 py-2 text-sm text-gray-400">
        {{ __('No categories found') }}
      </div>

      <!-- Create new -->
      <div
        v-if="canCreate"
        class="cursor-pointer border-t border-gray-100 px-3 py-2 text-sm font-medium text-accent-600 hover:bg-accent-50"
        @mousedown.prevent="createNew"
      >
        {{ creating ? __('Creating...') : __('Create') + ' "' + search.trim() + '"' }}
      </div>
    </div>
  </div>
</template>
