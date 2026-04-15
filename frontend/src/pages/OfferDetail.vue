<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import CapacityWidget from '@/components/CapacityWidget.vue'
import OfferAcceptedCard from '@/components/moments/OfferAcceptedCard.vue'
import FirstOfferSentOverlay from '@/components/moments/FirstOfferSentOverlay.vue'
import type { MicroOfferDraft, MicroOfferItem, MicroArticle, MicroCustomer } from '@/types/micro'

const props = defineProps<{
  id: string
}>()

const route = useRoute()

// Testing overrides via query params:
//   ?moment=accepted   — force show the Accepted card on any offer
//   ?moment=first-sent — force show the First Offer Sent overlay
const momentOverride = route.query.moment as string | undefined
const forceAccepted = momentOverride === 'accepted'
const forceFirstSent = momentOverride === 'first-sent'

const showAcceptedCard = ref(true)
const showFirstSentOverlay = ref(true)
const editing = ref(false)
const saving = ref(false)
const error = ref('')

// Edit form state
interface EditItem {
  article: string
  description: string
  quantity: number
  unit: string
  rate: number
}

const editForm = ref({
  title: '',
  contact: '',
  valid_until: '',
  status: 'Draft' as string,
  notes: '',
  internal_notes: '',
})
const editItems = ref<EditItem[]>([])

const offer = createResource({
  url: 'micro.api.offers.get_offer',
  params: { offer_id: props.id },
  auto: true,
  transform(data: { offer: MicroOfferDraft }) {
    return data.offer
  },
})

// Fetch customers and articles for edit mode selects
const customers = createResource({
  url: 'micro.api.customers.get_customers',
  params: { limit_page_length: 200, fields: ['name', 'first_name', 'last_name'] },
  transform(data: { customers: MicroCustomer[]; total: number }) {
    return data.customers
  },
})

const articles = createResource({
  url: 'micro.api.articles.get_articles',
  params: { limit_page_length: 200 },
  transform(data: { articles: MicroArticle[]; total: number }) {
    return data.articles
  },
})

const editTotal = computed(() =>
  editItems.value.reduce((sum, item) => sum + item.quantity * item.rate, 0),
)

const isEditValid = computed(() => {
  if (!editForm.value.contact) return false
  if (editItems.value.length === 0) return false
  return editItems.value.every((item) => item.description.trim() && item.quantity > 0 && item.rate > 0)
})

function startEditing() {
  if (!offer.data) return
  // Load dropdowns on first edit
  if (!customers.data) customers.reload()
  if (!articles.data) articles.reload()

  editForm.value = {
    title: offer.data.title || '',
    contact: offer.data.contact || '',
    valid_until: offer.data.valid_until || '',
    status: offer.data.status || 'Draft',
    notes: offer.data.notes || '',
    internal_notes: offer.data.internal_notes || '',
  }
  editItems.value = (offer.data.items as MicroOfferItem[]).map((item) => ({
    article: item.article || '',
    description: item.description,
    quantity: item.quantity,
    unit: item.unit || '',
    rate: item.rate,
  }))
  error.value = ''
  editing.value = true
}

function cancelEditing() {
  editing.value = false
  error.value = ''
}

function addItem() {
  editItems.value.push({ article: '', description: '', quantity: 1, unit: '', rate: 0 })
}

function removeItem(index: number) {
  if (editItems.value.length > 1) {
    editItems.value.splice(index, 1)
  }
}

function onArticleChange(index: number) {
  const articleName = editItems.value[index].article
  if (!articleName || !articles.data) return
  const article = articles.data.find((a: MicroArticle) => a.name === articleName)
  if (article) {
    editItems.value[index].description = article.description || article.article_name
    editItems.value[index].rate = article.selling_price || 0
    editItems.value[index].unit = article.unit || ''
  }
}

const updateOffer = createResource({
  url: 'micro.api.offers.update_offer',
  onSuccess() {
    saving.value = false
    editing.value = false
    offer.reload()
  },
  onError(err: { messages?: string[] }) {
    saving.value = false
    error.value = err.messages?.[0] || __('Failed to save offer')
  },
})

function saveEdit() {
  if (!isEditValid.value) return
  error.value = ''
  saving.value = true

  updateOffer.submit({
    offer_id: props.id,
    title: editForm.value.title.trim() || '',
    contact: editForm.value.contact,
    valid_until: editForm.value.valid_until || '',
    status: editForm.value.status,
    notes: editForm.value.notes,
    internal_notes: editForm.value.internal_notes,
    items: editItems.value.map((item) => ({
      article: item.article || undefined,
      description: item.description.trim(),
      quantity: item.quantity,
      rate: item.rate,
      unit: item.unit,
    })),
  })
}

// Quick status transitions (no edit mode needed)
const statusTransitioning = ref(false)

const statusTransition = createResource({
  url: 'micro.api.offers.update_offer',
  onSuccess() {
    statusTransitioning.value = false
    showAcceptedCard.value = true
    showFirstSentOverlay.value = true
    offer.reload()
  },
  onError(err: { messages?: string[] }) {
    statusTransitioning.value = false
    error.value = err.messages?.[0] || __('Failed to update status')
  },
})

function changeStatus(newStatus: string) {
  statusTransitioning.value = true
  error.value = ''
  statusTransition.submit({ offer_id: props.id, status: newStatus })
}

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '—'
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
}

const statusColors: Record<string, string> = {
  Draft: 'bg-gray-100 text-gray-700',
  Sent: 'bg-blue-100 text-blue-800',
  Accepted: 'bg-green-100 text-green-800',
  Declined: 'bg-red-100 text-red-800',
  Expired: 'bg-yellow-100 text-yellow-800',
}

const statuses = ['Draft', 'Sent', 'Accepted', 'Declined', 'Expired']
</script>

<template>
  <div v-if="offer.loading" class="py-12 text-center text-sm text-gray-500">
    {{ __('Loading...') }}
  </div>

  <div v-else-if="offer.error" class="py-12 text-center">
    <p class="text-sm text-red-500">{{ __('Failed to load offer') }}</p>
    <router-link to="/micro/offers" class="mt-2 inline-block text-sm text-gray-500 hover:text-gray-700">
      &larr; {{ __('Back to Offer Drafts') }}
    </router-link>
  </div>

  <div v-else-if="offer.data">
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
      </div>

      <div class="mt-2 flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">
            {{ offer.data.title || offer.data.reference }}
          </h1>
          <p class="mt-1 text-sm text-gray-500">{{ offer.data.reference }}</p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Watermark badge (G1 compliance) -->
          <span class="rounded-md bg-amber-50 px-3 py-1 text-sm font-bold text-amber-700 ring-1 ring-amber-200">
            {{ offer.data.watermark_text }}
          </span>
          <span
            v-if="!editing"
            class="inline-flex rounded-full px-3 py-1 text-sm font-medium"
            :class="statusColors[offer.data.status] || 'bg-gray-100 text-gray-700'"
          >
            {{ __(offer.data.status) }}
          </span>
          <!-- View mode buttons -->
          <template v-if="!editing">
            <!-- Status action buttons -->
            <button
              v-if="offer.data.status === 'Draft'"
              :disabled="statusTransitioning"
              class="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              @click="changeStatus('Sent')"
            >
              {{ statusTransitioning ? __('Updating...') : __('Mark as Sent') }}
            </button>
            <template v-if="offer.data.status === 'Sent'">
              <button
                :disabled="statusTransitioning"
                class="rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                @click="changeStatus('Accepted')"
              >
                {{ __('Accepted') }}
              </button>
              <button
                :disabled="statusTransitioning"
                class="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                @click="changeStatus('Declined')"
              >
                {{ __('Declined') }}
              </button>
            </template>
            <button
              class="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
              @click="startEditing"
            >
              {{ __('Edit') }}
            </button>
          </template>
          <!-- Edit mode buttons -->
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

    <!-- Emotional design moments -->
    <OfferAcceptedCard
      v-if="!editing && (offer.data?.status === 'Accepted' || forceAccepted) && showAcceptedCard"
      :offer-id="id"
      class="mb-4"
      @dismiss="showAcceptedCard = false"
    />
    <FirstOfferSentOverlay
      v-if="!editing && (offer.data?.status === 'Sent' || forceFirstSent) && showFirstSentOverlay"
      :force="forceFirstSent"
      @dismiss="showFirstSentOverlay = false"
    />

    <!-- Capacity hint for draft/sent offers -->
    <CapacityWidget
      v-if="!editing && (offer.data.status === 'Draft' || offer.data.status === 'Sent')"
      :compact="true"
      class="mb-4"
    />

    <!-- ═══════════════════ VIEW MODE ═══════════════════ -->
    <template v-if="!editing">
      <!-- Meta cards -->
      <div class="mb-6 grid grid-cols-4 gap-4">
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <div class="text-xs font-medium uppercase text-gray-500">{{ __('Contact') }}</div>
          <div class="mt-1 text-sm font-medium text-gray-900">{{ offer.data.contact }}</div>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <div class="text-xs font-medium uppercase text-gray-500">{{ __('Date') }}</div>
          <div class="mt-1 text-sm text-gray-900">{{ offer.data.date }}</div>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <div class="text-xs font-medium uppercase text-gray-500">{{ __('Valid Until') }}</div>
          <div class="mt-1 text-sm text-gray-900">{{ offer.data.valid_until || '—' }}</div>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-4">
          <div class="text-xs font-medium uppercase text-gray-500">{{ __('Total') }}</div>
          <div class="mt-1 text-lg font-bold text-gray-900">{{ formatCurrency(offer.data.total) }}</div>
        </div>
      </div>

      <!-- Items table -->
      <div class="mb-6 overflow-hidden rounded-lg border border-gray-200 bg-white">
        <div class="border-b border-gray-200 bg-gray-50 px-4 py-3">
          <h2 class="text-sm font-medium text-gray-700">{{ __('Items') }}</h2>
        </div>
        <table class="min-w-full divide-y divide-gray-200">
          <thead>
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                {{ __('Description') }}
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                {{ __('Qty') }}
              </th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                {{ __('Unit') }}
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                {{ __('Rate') }}
              </th>
              <th class="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                {{ __('Amount') }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="(item, idx) in (offer.data.items as MicroOfferItem[])" :key="idx">
              <td class="px-4 py-3 text-sm text-gray-900">{{ item.description }}</td>
              <td class="px-4 py-3 text-right text-sm text-gray-700">{{ item.quantity }}</td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ item.unit || '' }}</td>
              <td class="px-4 py-3 text-right text-sm text-gray-700">{{ formatCurrency(item.rate) }}</td>
              <td class="px-4 py-3 text-right text-sm font-medium text-gray-900">{{ formatCurrency(item.amount) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t-2 border-gray-300">
              <td colspan="4" class="px-4 py-3 text-right text-sm font-medium text-gray-700">
                {{ __('Total') }}
              </td>
              <td class="px-4 py-3 text-right text-lg font-bold text-gray-900">
                {{ formatCurrency(offer.data.total) }}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- Notes -->
      <div v-if="offer.data.notes" class="mb-6 rounded-lg border border-gray-200 bg-white p-4">
        <h2 class="mb-2 text-sm font-medium text-gray-700">{{ __('Notes for Client') }}</h2>
        <p class="text-sm text-gray-600">{{ offer.data.notes }}</p>
      </div>

      <!-- G4: Disclaimer (always shown) -->
      <div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-center">
        <p class="text-xs italic text-amber-700">{{ offer.data.disclaimer }}</p>
      </div>
    </template>

    <!-- ═══════════════════ EDIT MODE ═══════════════════ -->
    <template v-else>
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
                v-model="editForm.contact"
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
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Title') }}</label>
              <input
                v-model="editForm.title"
                type="text"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Valid Until') }}</label>
              <input
                v-model="editForm.valid_until"
                type="date"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Status') }}</label>
              <select
                v-model="editForm.status"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              >
                <option v-for="s in statuses" :key="s" :value="s">{{ __(s) }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="rounded-lg border border-gray-200 bg-white p-5">
          <h3 class="mb-4 text-sm font-medium uppercase text-gray-500">{{ __('Notes') }}</h3>
          <div class="space-y-4">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Notes for Client') }}</label>
              <textarea
                v-model="editForm.notes"
                rows="3"
                :placeholder="__('Visible to the client...')"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              ></textarea>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">{{ __('Internal Notes') }}</label>
              <textarea
                v-model="editForm.internal_notes"
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
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">{{ __('Article') }}</th>
              <th class="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">{{ __('Description') }} <span class="text-red-500">*</span></th>
              <th class="w-24 px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">{{ __('Qty') }} <span class="text-red-500">*</span></th>
              <th class="w-28 px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">{{ __('Unit') }}</th>
              <th class="w-32 px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">{{ __('Rate') }} <span class="text-red-500">*</span></th>
              <th class="w-32 px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">{{ __('Amount') }}</th>
              <th class="w-12 px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="(item, index) in editItems" :key="index">
              <td class="px-4 py-2">
                <select
                  v-model="item.article"
                  class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                  @change="onArticleChange(index)"
                >
                  <option value="">—</option>
                  <option v-for="a in articles.data" :key="a.name" :value="a.name">{{ a.article_name }}</option>
                </select>
              </td>
              <td class="px-4 py-2">
                <input v-model="item.description" type="text" :placeholder="__('Description')" class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500" />
              </td>
              <td class="px-4 py-2">
                <input v-model.number="item.quantity" type="number" min="0" step="0.01" class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-right text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500" />
              </td>
              <td class="px-4 py-2">
                <input v-model="item.unit" type="text" :placeholder="__('Unit')" class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500" />
              </td>
              <td class="px-4 py-2">
                <input v-model.number="item.rate" type="number" min="0" step="0.01" class="w-full rounded-md border border-gray-300 px-2 py-1.5 text-right text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500" />
              </td>
              <td class="px-4 py-2 text-right text-sm font-medium text-gray-900">
                {{ formatCurrency(item.quantity * item.rate) }}
              </td>
              <td class="px-4 py-2">
                <button v-if="editItems.length > 1" class="text-gray-400 hover:text-red-500" :title="__('Remove item')" @click="removeItem(index)">&times;</button>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t-2 border-gray-300">
              <td colspan="5" class="px-4 py-3 text-right text-sm font-medium text-gray-700">{{ __('Total') }}</td>
              <td class="px-4 py-3 text-right text-lg font-bold text-gray-900">{{ formatCurrency(editTotal) }}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </template>
  </div>
</template>
