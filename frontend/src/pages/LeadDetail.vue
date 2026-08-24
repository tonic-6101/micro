<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import ContactPicker from '@/components/ContactPicker.vue'
import FieldLabel from '@/components/FieldLabel.vue'
import { expectedValueRange, maxExpectedValue } from '@/limits'
import { CALL_OUTCOMES, MICRO_SOURCES } from '@/types/micro'
import type {
  BestCallTimeResponse,
  CallAttempt,
  CallAttemptsResponse,
  CallOutcome,
  LeadDetailResponse,
  MicroPipelineStage,
  StagesListResponse,
} from '@/types/micro'

const props = defineProps<{ id: string }>()
const router = useRouter()

const lead = createResource({
  url: 'micro.api.leads.get_lead',
  params: { lead_id: props.id },
  auto: true,
  // The delete permission rides along with the lead so the page needs one call.
  transform(data: LeadDetailResponse) {
    return { ...data.lead, can_delete: data.can_delete }
  },
})

const isArchived = computed(() => lead.data?.status === 'Archived')
const canDelete = computed(() => Boolean(lead.data?.can_delete))

// Nothing in the trash gets edited — restore it first, then change it.
const canEdit = computed(() => Boolean(lead.data) && !isArchived.value)

// The stored status stays `Archived`; what the user reads is the bin.
const statusLabel = computed(() =>
  isArchived.value ? __('In trash') : __(lead.data?.status || ''),
)

const confirmingDelete = ref(false)
const actionError = ref('')

const archiveLead = createResource({ url: 'micro.api.leads.archive_lead' })
const restoreLead = createResource({ url: 'micro.api.leads.restore_lead' })
const deleteLead = createResource({ url: 'micro.api.leads.delete_lead' })

function onActionError(err: unknown, fallback: string) {
  actionError.value = (err as { messages?: string[] })?.messages?.[0] || fallback
}

function onArchive() {
  actionError.value = ''
  archiveLead
    .submit({ lead_id: props.id })
    .then(() => lead.reload())
    .catch((err: unknown) => onActionError(err, __('Failed to move lead to trash')))
}

function onRestore() {
  actionError.value = ''
  restoreLead
    .submit({ lead_id: props.id })
    .then(() => lead.reload())
    .catch((err: unknown) => onActionError(err, __('Failed to restore lead')))
}

function onDelete() {
  actionError.value = ''
  deleteLead
    .submit({ lead_id: props.id })
    .then(() => router.push('/micro/leads'))
    .catch((err: unknown) => {
      confirmingDelete.value = false
      onActionError(err, __('Failed to delete lead'))
    })
}

// --- inline editing --------------------------------------------------------
// One field at a time: click the value, change it, save. Same pattern as the
// Client Intelligence card on the contact page.

const editingField = ref<string | null>(null)
const editValue = ref('')
const contactValue = ref('')
const contactLabel = ref('')
const fieldError = ref('')

const updateLead = createResource({
  url: 'micro.api.leads.update_lead',
  onSuccess() {
    editingField.value = null
    lead.reload()
  },
  onError(err: { messages?: string[] }) {
    fieldError.value = err.messages?.[0] || __('Failed to update lead')
  },
})

// The lead stores a stage docname, so the picker needs the pipeline's real list.
const stages = createResource({
  url: 'micro.api.pipeline.get_stages',
  transform(data: StagesListResponse) {
    return data.stages
  },
})

const stageOptions = computed<MicroPipelineStage[]>(() => stages.data || [])

const contactName = computed(() => {
  const details = lead.data?.contact_details
  if (details) return details.full_name || details.company_name || details.name
  return lead.data?.contact || ''
})

const stageLabel = computed(() => lead.data?.stage_name || lead.data?.stage || '')

// Shown under the amount while editing — the answer to "0 to how much?"
const valueRange = computed(() => expectedValueRange())

const expectedValueLabel = computed(() => {
  const value = lead.data?.expected_value
  if (!value) return ''
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(value)
})

function startEdit(field: string, current?: string | number | null) {
  if (!canEdit.value) return
  fieldError.value = ''
  editValue.value = current === undefined || current === null ? '' : String(current)
  editingField.value = field
}

function startEditStage() {
  if (!canEdit.value) return
  stages.update({ params: { pipeline: lead.data?.pipeline || undefined } })
  stages.reload()
  startEdit('stage', lead.data?.stage)
}

function startEditContact() {
  if (!canEdit.value) return
  fieldError.value = ''
  contactValue.value = lead.data?.contact || ''
  contactLabel.value = contactName.value
  editingField.value = 'contact'
}

function cancelEdit() {
  editingField.value = null
  editValue.value = ''
  fieldError.value = ''
}

function saveField(field: string) {
  fieldError.value = ''
  updateLead.submit({ lead_id: props.id, [field]: editValue.value })
}

function saveContact() {
  fieldError.value = ''
  updateLead.submit({ lead_id: props.id, contact: contactValue.value })
}

// --- call attempts ----------------------------------------------------------
// Logged against the contact, not this lead: the same person runs through
// several deals over time, and when they tend to answer is a property of
// them, not of any one deal.

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const BUCKET_LABELS: Record<string, string> = {
  morning: 'Morning (6–12)',
  midday: 'Midday (12–14)',
  afternoon: 'Afternoon (14–18)',
  evening: 'Evening (18–21)',
  other: 'Other times',
}

const callAttempts = createResource({
  url: 'micro.api.call_attempts.get_call_attempts',
  transform(data: CallAttemptsResponse) {
    return data.attempts
  },
})

const bestTime = createResource({
  url: 'micro.api.call_attempts.get_best_time_to_call',
  transform(data: BestCallTimeResponse) {
    return data
  },
})

// The contact only becomes known once the lead has loaded.
watch(
  () => lead.data?.contact,
  (contact) => {
    if (!contact) return
    callAttempts.update({ params: { contact } })
    callAttempts.reload()
    bestTime.update({ params: { contact } })
    bestTime.reload()
  },
)

const loggingOutcome = ref('')
const callError = ref('')

const logAttempt = createResource({
  url: 'micro.api.call_attempts.log_call_attempt',
  onSuccess() {
    loggingOutcome.value = ''
    callAttempts.reload()
    bestTime.reload()
  },
  onError(err: { messages?: string[] }) {
    loggingOutcome.value = ''
    callError.value = err.messages?.[0] || __('Could not log this call')
  },
})

function logOutcome(outcome: CallOutcome) {
  if (!lead.data?.contact) return
  callError.value = ''
  loggingOutcome.value = outcome
  logAttempt.submit({ contact: lead.data.contact, lead: props.id, outcome })
}

function formatAttempt(attempt: CallAttempt): string {
  const dt = new Date(attempt.attempted_at.replace(' ', 'T'))
  const weekday = __(WEEKDAYS[(dt.getDay() + 6) % 7])
  const time = dt.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
  return `${weekday}, ${time}`
}

const recentAttempts = computed(() => (callAttempts.data || []).slice(0, 5))
</script>

<template>
  <div class="p-6">
    <router-link to="/micro/leads" class="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block">
      &larr; {{ __('Back to Leads') }}
    </router-link>

    <div v-if="lead.data" class="space-y-6">
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0 flex-1">
          <div v-if="editingField === 'lead_name'">
            <input
              v-model="editValue"
              type="text"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-lg font-semibold focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              @keyup.enter="saveField('lead_name')"
              @keydown.escape="cancelEdit"
            />
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('lead_name')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
          </div>
          <h1
            v-else
            class="-mx-2 truncate rounded-md px-2 py-0.5 text-xl font-semibold text-gray-900"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            :title="canEdit ? __('Rename lead') : ''"
            @click="startEdit('lead_name', lead.data.lead_name)"
          >
            {{ lead.data.lead_name }}
          </h1>
        </div>
        <FieldLabel field="status" :uppercase="false" align="right" class="shrink-0">
          <span
            class="rounded-full px-3 py-1 text-sm font-medium"
            :class="{
              'bg-green-100 text-green-800': lead.data.status === 'Won',
              'bg-red-100 text-red-800': lead.data.status === 'Lost',
              'bg-blue-100 text-blue-800': lead.data.status === 'Open',
              'bg-gray-100 text-gray-800': lead.data.status === 'Archived',
            }"
          >
            {{ statusLabel }}
          </span>
        </FieldLabel>
      </div>

      <!-- Say plainly that this one is binned, and offer the way back -->
      <div
        v-if="isArchived"
        class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3"
      >
        <p class="text-sm text-gray-600">
          {{ __('This lead is in the trash — it is hidden from the board and the lists. Restore it to make changes.') }}
        </p>
        <router-link to="/micro/leads/trash" class="text-xs text-gray-500 hover:text-gray-700">
          {{ __('Trash') }} &rarr;
        </router-link>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-if="!isArchived"
          type="button"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="archiveLead.loading"
          @click="onArchive"
        >
          {{ __('Move to trash') }}
        </button>
        <button
          v-else
          type="button"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          :disabled="restoreLead.loading"
          @click="onRestore"
        >
          {{ __('Restore') }}
        </button>

        <template v-if="canDelete">
          <button
            v-if="!confirmingDelete"
            type="button"
            class="rounded-md px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
            @click="confirmingDelete = true"
          >
            {{ __('Delete') }}
          </button>
          <template v-else>
            <span class="text-sm text-gray-600">{{ __('Delete for good?') }}</span>
            <button
              type="button"
              class="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              :disabled="deleteLead.loading"
              @click="onDelete"
            >
              {{ __('Yes, delete permanently') }}
            </button>
            <button
              type="button"
              class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              @click="confirmingDelete = false"
            >
              {{ __('Cancel') }}
            </button>
          </template>
        </template>
      </div>

      <p v-if="actionError" class="text-sm text-red-600">{{ actionError }}</p>

      <div class="grid grid-cols-2 gap-4 rounded-lg border border-gray-200 p-4">
        <!-- Contact -->
        <div>
          <FieldLabel field="contact" :label="__('Contact')" />
          <div v-if="editingField === 'contact'">
            <ContactPicker v-model="contactValue" v-model:label="contactLabel" />
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveContact"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            :title="canEdit ? __('Change contact') : ''"
            @click="startEditContact"
          >
            <router-link
              v-if="lead.data.contact"
              :to="`/micro/customers/${lead.data.contact}`"
              class="text-accent-600 hover:underline"
              @click.stop
            >
              {{ contactName }}
            </router-link>
            <span v-else class="text-gray-400">{{ __('Add contact') }}</span>
          </div>
        </div>

        <!-- Stage — the status follows from it, so it is never edited directly -->
        <div>
          <FieldLabel field="stage" :label="__('Stage')" />
          <div v-if="editingField === 'stage'">
            <select
              v-model="editValue"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700"
              @keydown.escape="cancelEdit"
            >
              <option v-if="stages.loading" value="">{{ __('Loading...') }}</option>
              <option v-for="stage in stageOptions" :key="stage.name" :value="stage.name">
                {{ __(stage.stage_name) }}
              </option>
            </select>
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('stage')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            @click="startEditStage"
          >
            <span v-if="stageLabel">{{ __(stageLabel) }}</span>
            <span v-else class="text-gray-400">{{ __('Click to set...') }}</span>
          </div>
        </div>

        <!-- Priority -->
        <div>
          <FieldLabel field="priority" :label="__('Priority')" />
          <div v-if="editingField === 'priority'">
            <select
              v-model="editValue"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700"
              @keydown.escape="cancelEdit"
            >
              <option value="Low">{{ __('Low') }}</option>
              <option value="Medium">{{ __('Medium') }}</option>
              <option value="High">{{ __('High') }}</option>
            </select>
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('priority')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            @click="startEdit('priority', lead.data.priority || 'Medium')"
          >
            <span v-if="lead.data.priority">{{ __(lead.data.priority) }}</span>
            <span v-else class="text-gray-400">{{ __('Click to set...') }}</span>
          </div>
        </div>

        <!-- Expected value -->
        <div>
          <FieldLabel field="expected_value" :label="__('Expected Value')" />
          <div v-if="editingField === 'expected_value'">
            <input
              v-model="editValue"
              type="number"
              min="0"
              :max="maxExpectedValue() || undefined"
              step="0.01"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              @keyup.enter="saveField('expected_value')"
              @keydown.escape="cancelEdit"
            />
            <p v-if="valueRange" class="mt-1 text-xs text-gray-400">{{ valueRange }}</p>
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('expected_value')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            @click="startEdit('expected_value', lead.data.expected_value)"
          >
            <span v-if="expectedValueLabel">{{ expectedValueLabel }}</span>
            <span v-else class="text-gray-400">{{ __('Click to set...') }}</span>
          </div>
        </div>

        <!-- Source -->
        <div>
          <FieldLabel field="source" :label="__('Source')" />
          <div v-if="editingField === 'source'">
            <select
              v-model="editValue"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700"
              @keydown.escape="cancelEdit"
            >
              <option value="">{{ __('Not set') }}</option>
              <option v-for="s in MICRO_SOURCES" :key="s" :value="s">{{ __(s) }}</option>
            </select>
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('source')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            @click="startEdit('source', lead.data.source)"
          >
            <span v-if="lead.data.source">{{ __(lead.data.source) }}</span>
            <span v-else class="text-gray-400">{{ __('Click to set...') }}</span>
          </div>
        </div>

        <!-- Next follow-up -->
        <div>
          <FieldLabel field="next_follow_up" :label="__('Next Follow-up')" />
          <div v-if="editingField === 'next_follow_up'">
            <input
              v-model="editValue"
              type="date"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              @keyup.enter="saveField('next_follow_up')"
              @keydown.escape="cancelEdit"
            />
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('next_follow_up')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            @click="startEdit('next_follow_up', lead.data.next_follow_up)"
          >
            <span v-if="lead.data.next_follow_up">{{ lead.data.next_follow_up }}</span>
            <span v-else class="text-gray-400">{{ __('Click to set...') }}</span>
          </div>
        </div>

        <!-- Lost reason — only asked for once the deal is lost, but then required -->
        <div v-if="lead.data.status === 'Lost' || lead.data.lost_reason" class="col-span-2">
          <FieldLabel field="lost_reason" :label="__('Lost Reason')" />
          <div v-if="editingField === 'lost_reason'">
            <input
              v-model="editValue"
              type="text"
              class="w-full rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
              @keyup.enter="saveField('lost_reason')"
              @keydown.escape="cancelEdit"
            />
            <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
            <div class="mt-1 flex gap-1">
              <button
                class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                :disabled="updateLead.loading"
                @click="saveField('lost_reason')"
              >
                {{ __('Save') }}
              </button>
              <button
                class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                @click="cancelEdit"
              >
                {{ __('Cancel') }}
              </button>
            </div>
          </div>
          <div
            v-else
            class="-mx-2 rounded-md px-2 py-0.5 text-sm font-medium"
            :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
            @click="startEdit('lost_reason', lead.data.lost_reason)"
          >
            <span v-if="lead.data.lost_reason">{{ lead.data.lost_reason }}</span>
            <span v-else class="text-gray-400">{{ __('Click to add...') }}</span>
          </div>
        </div>
      </div>

      <!-- Call attempts: log one now, and see when this contact tends to pick up -->
      <div v-if="lead.data.contact" class="rounded-lg border border-gray-200 p-4">
        <FieldLabel field="log_call_attempt" :label="__('Call Attempts')" class="mb-2" />

        <div class="flex flex-wrap gap-2">
          <button
            v-for="outcome in CALL_OUTCOMES"
            :key="outcome"
            type="button"
            class="rounded-md border px-3 py-1.5 text-sm font-medium disabled:opacity-50"
            :class="
              outcome === 'Reached'
                ? 'border-green-600 bg-green-50 text-green-700 hover:bg-green-100'
                : 'border-gray-300 text-gray-700 hover:bg-gray-50'
            "
            :disabled="Boolean(loggingOutcome) || isArchived"
            @click="logOutcome(outcome)"
          >
            {{ loggingOutcome === outcome ? __('Logging...') : __(outcome) }}
          </button>
        </div>
        <p v-if="callError" class="mt-2 text-xs text-red-600">{{ callError }}</p>

        <!-- Best time: only once there is something worth trusting -->
        <div v-if="bestTime.data?.best" class="mt-3 rounded-md bg-green-50 px-3 py-2">
          <FieldLabel field="best_time_to_call" :uppercase="false" class="text-sm font-medium text-green-800">
            {{ __('Best time to reach:') }}
            {{ __(WEEKDAYS[bestTime.data.best.weekday]) }}, {{ __(BUCKET_LABELS[bestTime.data.best.bucket]) }}
          </FieldLabel>
          <p class="mt-0.5 text-xs text-green-700">
            {{
              __('Reached {reached} of {attempts} times in this slot', {
                reached: String(bestTime.data.best.reached),
                attempts: String(bestTime.data.best.attempts),
              })
            }}
          </p>
        </div>
        <p
          v-else-if="bestTime.data && bestTime.data.total_attempts > 0"
          class="mt-3 text-xs text-gray-400"
        >
          {{ __('Not enough of a pattern yet — keep logging attempts.') }}
        </p>

        <!-- Recent attempts -->
        <ul v-if="recentAttempts.length" class="mt-3 space-y-1 border-t border-gray-100 pt-3">
          <li
            v-for="attempt in recentAttempts"
            :key="attempt.name"
            class="flex items-center justify-between text-sm text-gray-600"
          >
            <span>{{ formatAttempt(attempt) }}</span>
            <span
              class="rounded-full px-2 py-0.5 text-xs font-medium"
              :class="attempt.outcome === 'Reached' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'"
            >
              {{ __(attempt.outcome) }}
            </span>
          </li>
        </ul>
      </div>

      <!-- Notes: always on the page, whether or not anything is written yet -->
      <div class="rounded-lg border border-gray-200 p-4">
        <FieldLabel field="notes" :label="__('Notes')" class="mb-2" />
        <div v-if="editingField === 'notes'">
          <textarea
            v-model="editValue"
            rows="6"
            class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
            :placeholder="__('What was said, what was agreed, what comes next...')"
            @keydown.escape="cancelEdit"
          />
          <p v-if="fieldError" class="mt-1 text-xs text-red-600">{{ fieldError }}</p>
          <div class="mt-1 flex gap-1">
            <button
              class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
              :disabled="updateLead.loading"
              @click="saveField('notes')"
            >
              {{ __('Save') }}
            </button>
            <button
              class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
              @click="cancelEdit"
            >
              {{ __('Cancel') }}
            </button>
          </div>
        </div>
        <div
          v-else-if="lead.data.notes"
          class="-mx-2 whitespace-pre-wrap rounded-md px-2 py-1 text-sm text-gray-700"
          :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
          :title="canEdit ? __('Edit notes') : ''"
          @click="startEdit('notes', lead.data.notes)"
          v-html="lead.data.notes"
        ></div>
        <p
          v-else
          class="-mx-2 rounded-md px-2 py-1 text-sm italic text-gray-400"
          :class="canEdit ? 'cursor-pointer hover:bg-gray-50' : ''"
          @click="startEdit('notes', '')"
        >
          {{ __('Click to add...') }}
        </p>
      </div>
    </div>

    <div v-else-if="lead.loading" class="text-center text-gray-500 py-8">
      {{ __('Loading...') }}
    </div>
  </div>
</template>
