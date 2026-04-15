<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroArticle, MicroCustomer } from '@/types/micro'

const router = useRouter()

interface OfferItemForm {
  article: string
  description: string
  quantity: number
  unit: string
  rate: number
}

const form = ref({
  contact: '',
  title: '',
  notes: '',
  internal_notes: '',
})

const items = ref<OfferItemForm[]>([
  { article: '', description: '', quantity: 1, unit: '', rate: 0 },
])

const error = ref('')
const submitting = ref(false)

const isValid = computed(() => {
  if (!form.value.contact) return false
  if (items.value.length === 0) return false
  return items.value.every((item) => item.description.trim() && item.quantity > 0 && item.rate > 0)
})

const total = computed(() =>
  items.value.reduce((sum, item) => sum + item.quantity * item.rate, 0),
)

// Fetch customers for contact picker
const customers = createResource({
  url: 'micro.api.customers.get_customers',
  params: { limit_page_length: 200, fields: ['name', 'first_name', 'last_name'] },
  auto: true,
  transform(data: { customers: MicroCustomer[]; total: number }) {
    return data.customers
  },
})

// Fetch articles for article picker
const articles = createResource({
  url: 'micro.api.articles.get_articles',
  params: { limit_page_length: 200 },
  auto: true,
  transform(data: { articles: MicroArticle[]; total: number }) {
    return data.articles
  },
})

function addItem() {
  items.value.push({ article: '', description: '', quantity: 1, unit: '', rate: 0 })
}

function removeItem(index: number) {
  if (items.value.length > 1) {
    items.value.splice(index, 1)
  }
}

function onArticleChange(index: number) {
  const articleName = items.value[index].article
  if (!articleName || !articles.data) return

  const article = articles.data.find((a: MicroArticle) => a.name === articleName)
  if (article) {
    items.value[index].description = article.description || article.article_name
    items.value[index].rate = article.selling_price || 0
    items.value[index].unit = article.unit || ''
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

const createOffer = createResource({
  url: 'micro.api.offers.create_offer',
  onSuccess(data: { offer: { name: string } }) {
    router.push(`/micro/offers/${data.offer.name}`)
  },
  onError(err: { messages?: string[] }) {
    submitting.value = false
    error.value = err.messages?.[0] || __('Failed to create offer')
  },
})

function submit() {
  if (!form.value.contact) {
    error.value = __('Customer is required')
    return
  }
  if (!items.value.some((item) => item.description.trim())) {
    error.value = __('At least one item with a description is required')
    return
  }

  error.value = ''
  submitting.value = true

  createOffer.submit({
    contact: form.value.contact,
    title: form.value.title.trim() || undefined,
    items: items.value.map((item) => ({
      article: item.article || undefined,
      description: item.description.trim(),
      quantity: item.quantity,
      rate: item.rate,
      unit: item.unit,
    })),
  })
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center gap-3">
        <router-link
          to="/micro/offers"
          class="text-sm text-gray-500 hover:text-gray-700"
        >
          {{ __('Offer Drafts') }}
        </router-link>
        <span class="text-gray-300">/</span>
        <span class="text-sm text-gray-700">{{ __('New Offer Draft') }}</span>
      </div>

      <div class="mt-2 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">
          {{ __('New Offer Draft') }}
        </h1>
        <div class="flex items-center gap-3">
          <router-link
            to="/micro/offers"
            class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {{ __('Cancel') }}
          </router-link>
          <button
            :disabled="!isValid || submitting"
            class="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-50"
            @click="submit"
          >
            {{ submitting ? __('Saving...') : __('Create Offer') }}
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
      <!-- Offer Details -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Offer Details') }}</h3>

        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Customer') }} <span class="text-red-500">*</span>
            </label>
            <select
              v-model="form.contact"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            >
              <option value="">{{ __('Select customer...') }}</option>
              <option
                v-for="customer in customers.data"
                :key="customer.name"
                :value="customer.name"
              >
                {{ customer.full_name || customer.first_name }}
              </option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Title') }}
            </label>
            <input
              v-model="form.title"
              type="text"
              :placeholder="__('Offer title (optional)')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            />
          </div>
        </div>
      </div>

      <!-- Notes -->
      <div class="rounded-lg border border-gray-200 bg-white p-5">
        <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Notes') }}</h3>

        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Notes for Client') }}
            </label>
            <textarea
              v-model="form.notes"
              rows="3"
              :placeholder="__('Visible to the client...')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            ></textarea>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">
              {{ __('Internal Notes') }}
            </label>
            <textarea
              v-model="form.internal_notes"
              rows="3"
              :placeholder="__('Only visible to you...')"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            ></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Items -->
    <div class="mt-6 rounded-lg border border-gray-200 bg-white">
      <div class="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
        <h3 class="text-sm font-medium text-gray-700">{{ __('Items') }}</h3>
        <button
          class="rounded-md border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100"
          @click="addItem"
        >
          + {{ __('Add Item') }}
        </button>
      </div>

      <table class="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Article') }}
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Description') }} <span class="text-red-500">*</span>
            </th>
            <th class="w-24 px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Qty') }} <span class="text-red-500">*</span>
            </th>
            <th class="w-28 px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
              {{ __('Unit') }}
            </th>
            <th class="w-32 px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Rate') }} <span class="text-red-500">*</span>
            </th>
            <th class="w-32 px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
              {{ __('Amount') }}
            </th>
            <th class="w-12 px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="(item, index) in items" :key="index">
            <td class="px-4 py-2">
              <select
                v-model="item.article"
                class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                @change="onArticleChange(index)"
              >
                <option value="">—</option>
                <option
                  v-for="article in articles.data"
                  :key="article.name"
                  :value="article.name"
                >
                  {{ article.article_name }}
                </option>
              </select>
            </td>
            <td class="px-4 py-2">
              <input
                v-model="item.description"
                type="text"
                :placeholder="__('Description')"
                class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </td>
            <td class="px-4 py-2">
              <input
                v-model.number="item.quantity"
                type="number"
                min="0"
                step="0.01"
                class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-right text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </td>
            <td class="px-4 py-2">
              <input
                v-model="item.unit"
                type="text"
                :placeholder="__('Unit')"
                class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </td>
            <td class="px-4 py-2">
              <input
                v-model.number="item.rate"
                type="number"
                min="0"
                step="0.01"
                class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-right text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </td>
            <td class="px-4 py-2 text-right text-sm font-medium text-gray-900">
              {{ formatCurrency(item.quantity * item.rate) }}
            </td>
            <td class="px-4 py-2">
              <button
                v-if="items.length > 1"
                class="text-gray-400 hover:text-red-500"
                :title="__('Remove item')"
                @click="removeItem(index)"
              >
                &times;
              </button>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="border-t-2 border-gray-300">
            <td colspan="5" class="px-4 py-3 text-right text-sm font-medium text-gray-700">
              {{ __('Total') }}
            </td>
            <td class="px-4 py-3 text-right text-lg font-bold text-gray-900">
              {{ formatCurrency(total) }}
            </td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>
