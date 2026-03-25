<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroArticle } from '@/types/micro'

const search = ref('')
const page = ref(1)
const pageSize = 20

const articles = createResource({
  url: 'micro.api.articles.get_articles',
  params: {
    limit_start: 0,
    limit_page_length: pageSize,
    search: search.value,
  },
  auto: true,
  transform(data: { articles: MicroArticle[]; total: number }) {
    return data
  },
})

watch([search, page], () => {
  articles.update({
    params: {
      limit_start: (page.value - 1) * pageSize,
      limit_page_length: pageSize,
      search: search.value,
    },
  })
  articles.reload()
})

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">
        {{ __('Articles') }}
      </h1>
      <a
        href="/app/micro-article/new"
        class="rounded-md bg-accent-600 px-3 py-2 text-sm font-medium text-white hover:bg-accent-700"
      >
        {{ __('New Article') }}
      </a>
    </div>

    <!-- Search -->
    <div class="mb-4">
      <input
        v-model="search"
        type="text"
        :placeholder="__('Search articles...')"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
      />
    </div>

    <!-- Articles list -->
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Article') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Code') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Category') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('VK') }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('EK') }}
            </th>
            <th class="px-4 py-3 text-center text-xs font-medium uppercase text-gray-500">
              {{ __('Active') }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="article in articles.data?.articles"
            :key="article.name"
            class="cursor-pointer hover:bg-gray-50"
            @click="$router.push(`/app/micro-article/${article.name}`)"
          >
            <td class="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
              {{ article.article_name }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ article.article_code || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
              {{ article.category || '—' }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-900">
              {{ formatCurrency(article.selling_price) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm text-gray-500">
              {{ formatCurrency(article.purchase_price) }}
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-center text-sm">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                :class="article.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'"
              >
                {{ article.is_active ? __('Active') : __('Inactive') }}
              </span>
            </td>
          </tr>

          <tr v-if="articles.loading">
            <td colspan="6" class="px-4 py-8 text-center text-sm text-gray-500">
              {{ __('Loading...') }}
            </td>
          </tr>

          <tr v-else-if="articles.error">
            <td colspan="6" class="px-4 py-8 text-center text-sm text-red-500">
              {{ __('Failed to load articles. Please try again.') }}
            </td>
          </tr>

          <tr v-else-if="!articles.data?.articles?.length">
            <td colspan="6" class="px-4 py-12 text-center">
              <p class="text-sm text-gray-500">{{ search ? __('No articles match your search') : __('No articles yet') }}</p>
              <a
                v-if="!search"
                href="/app/micro-article/new"
                class="mt-2 inline-block text-sm font-medium text-gray-900 hover:text-gray-700"
              >
                {{ __('Create your first article') }} &rarr;
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="articles.data?.total && articles.data.total > pageSize"
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
        :disabled="page * pageSize >= articles.data.total"
        class="rounded-md border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
        @click="page++"
      >
        {{ __('Next') }}
      </button>
    </div>
  </div>
</template>
