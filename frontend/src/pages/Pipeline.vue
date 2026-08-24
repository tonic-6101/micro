<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import { MICRO_SOURCES } from '@/types/micro'
import type { MicroLead, PipelineResponse, PipelinesListResponse } from '@/types/micro'
import FieldLabel from '@/components/FieldLabel.vue'
import KanbanColumn from '@/components/pipeline/KanbanColumn.vue'
import LeadDialog from '@/components/pipeline/LeadDialog.vue'
import PipelineManager from '@/components/pipeline/PipelineManager.vue'

const route = useRoute()
const router = useRouter()

// The pipeline tabs carry the target group — a segment filter inside a board
// would only re-filter what the board already is.
const activePipeline = ref<string>((route.params.pipelineId as string) || '')
const showClosed = ref(false)
const source = ref('')
const priority = ref('')
const dueOnly = ref(false)

// What the user types, and the term the board is actually queried with. Every
// keystroke would otherwise refetch one query per column.
const searchInput = ref('')
const search = ref('')
let searchDebounce: ReturnType<typeof setTimeout> | undefined

const managing = ref('')
const creating = ref(false)
const newPipelineName = ref('')
const createError = ref('')

// null = dialog closed. A set `stage` means the card was started from a column;
// an empty one lets the controller drop it in the first open stage.
const addingLead = ref<{ stage: string; stageName: string } | null>(null)

const pipelines = createResource({
  url: 'micro.api.pipeline.get_pipelines',
  auto: true,
  transform(data: PipelinesListResponse) {
    return data
  },
  onSuccess(data: PipelinesListResponse) {
    if (!activePipeline.value) {
      activePipeline.value = data.default || data.pipelines[0]?.name || ''
    }
  },
})

const pipeline = createResource({
  url: 'micro.api.pipeline.get_pipeline',
  transform(data: PipelineResponse) {
    return data
  },
})

const createPipeline = createResource({ url: 'micro.api.pipeline_admin.create_pipeline' })

const moveLead = createResource({
  url: 'micro.api.pipeline.move_lead',
})

const boardParams = computed(() => ({
  pipeline: activePipeline.value || undefined,
  show_closed: showClosed.value,
  source: source.value || undefined,
  priority: priority.value || undefined,
  due_only: dueOnly.value,
  search: search.value || undefined,
}))

const totalValue = computed(() => {
  const value = pipeline.data?.totals?.value || 0
  if (!value) return ''
  return value.toLocaleString('de-DE', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  })
})

const hasFilters = computed(() =>
  Boolean(source.value || priority.value || dueOnly.value || search.value),
)

// A hit can sit in a won or lost stage, which the board hides by default —
// say so rather than let the search look empty.
const searchFoundNothing = computed(
  () => Boolean(search.value) && !pipeline.loading && pipeline.data?.totals?.count === 0,
)

function reloadBoard() {
  if (!activePipeline.value) return
  pipeline.update({ params: boardParams.value })
  pipeline.reload()
}

watch(
  boardParams,
  () => {
    reloadBoard()
  },
  { deep: true, immediate: true },
)

watch(searchInput, (value) => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    search.value = value.trim()
  }, 250)
})

onBeforeUnmount(() => clearTimeout(searchDebounce))

watch(activePipeline, (value) => {
  if (value && route.params.pipelineId !== value) {
    router.replace(`/micro/pipeline/${value}`)
  }
})

watch(
  () => route.params.pipelineId,
  (value) => {
    if (value && value !== activePipeline.value) {
      activePipeline.value = value as string
    }
  },
)

function clearFilters() {
  source.value = ''
  priority.value = ''
  dueOnly.value = false
  clearSearch()
}

function clearSearch() {
  clearTimeout(searchDebounce)
  searchInput.value = ''
  search.value = ''
}

function startCreate() {
  creating.value = true
  createError.value = ''
  newPipelineName.value = ''
}

function onCreatePipeline() {
  const pipelineName = newPipelineName.value.trim()
  if (!pipelineName) return

  createPipeline
    .submit({ pipeline_name: pipelineName, with_starter_stages: true })
    .then((result: { pipeline: string }) => {
      creating.value = false
      pipelines.reload()
      activePipeline.value = result.pipeline
      reloadBoard()
    })
    .catch((error: unknown) => {
      createError.value = (error as { messages?: string[] })?.messages?.[0] || String(error)
    })
}

function startAddLead(stage = '', stageName = '') {
  addingLead.value = { stage, stageName }
}

function onLeadCreated() {
  addingLead.value = null
  reloadBoard()
  // The tab badges count open leads.
  pipelines.reload()
}

function onPipelineChanged(name: string) {
  managing.value = ''
  pipelines.reload()
  activePipeline.value = name
  reloadBoard()
}

function onPipelineDeleted() {
  managing.value = ''
  activePipeline.value = ''
  pipelines.reload()
  router.replace('/micro/pipeline')
}

function onDrop(leadId: string, stageId: string) {
  // Optimistic update: move the card locally, then persist.
  const data = pipeline.data as PipelineResponse | undefined
  if (data) {
    let moved: MicroLead | null = null

    for (const col of data.stages) {
      const idx = col.leads.findIndex((l) => l.name === leadId)
      if (idx !== -1) {
        moved = col.leads.splice(idx, 1)[0]
        // `count` is the whole column, not the page on screen — adjust it,
        // never recompute it from the cards that happen to be loaded.
        col.count -= 1
        col.loaded = col.leads.length
        break
      }
    }

    if (!moved) {
      const idx = data.unassigned.findIndex((l) => l.name === leadId)
      if (idx !== -1) {
        moved = data.unassigned.splice(idx, 1)[0]
      }
    }

    if (moved) {
      const target = data.stages.find((col) => col.stage.name === stageId)
      if (target) {
        moved.stage = stageId
        target.leads.unshift(moved)
        target.count += 1
        target.loaded = target.leads.length
      }
    }
  }

  // A win/loss stage rewrites status and may demand a loss reason — always
  // reconcile with the server rather than trusting the optimistic move.
  moveLead
    .submit({ lead_id: leadId, stage_id: stageId })
    .then(() => reloadBoard())
    .catch(() => reloadBoard())
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="mb-3 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          {{ __('Pipeline') }}
        </h1>
        <p v-if="pipeline.data?.totals" class="mt-0.5 text-xs text-gray-500">
          {{ pipeline.data.totals.count }} {{ __('leads') }}
          <span v-if="totalValue"> &middot; {{ totalValue }}</span>
        </p>
      </div>
      <div class="flex items-center gap-3">
        <button
          v-if="activePipeline"
          type="button"
          class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
          @click="startAddLead()"
        >
          {{ __('New Lead') }}
        </button>
        <router-link
          :to="activePipeline ? `/micro/call-list/${activePipeline}` : '/micro/call-list'"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          {{ __('Call List') }}
        </router-link>
        <button
          v-if="activePipeline"
          type="button"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          @click="managing = activePipeline"
        >
          {{ __('Edit Pipeline') }}
        </button>
      </div>
    </div>

    <!-- Pipeline tabs -->
    <div
      v-if="pipelines.data?.pipelines?.length"
      class="mb-3 flex items-center gap-1 overflow-x-auto border-b border-gray-200"
    >
      <button
        v-for="p in pipelines.data.pipelines"
        :key="p.name"
        type="button"
        class="flex shrink-0 items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium transition"
        :class="
          p.name === activePipeline
            ? 'border-gray-900 text-gray-900'
            : 'border-transparent text-gray-500 hover:text-gray-700'
        "
        @click="activePipeline = p.name"
      >
        {{ p.pipeline_name }}
        <span
          class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-gray-100 px-1.5 text-[10px] font-medium text-gray-600"
        >
          {{ p.open_leads }}
        </span>
        <span
          v-if="p.name === activePipeline"
          class="text-gray-400 hover:text-gray-900"
          :title="__('Edit Pipeline')"
          @click.stop="managing = p.name"
        >
          &#9881;
        </span>
      </button>

      <!-- Add pipeline -->
      <button
        type="button"
        class="shrink-0 border-b-2 border-transparent px-3 py-2 text-sm font-medium text-gray-400 hover:text-gray-900"
        :title="__('New pipeline')"
        @click="startCreate"
      >
        +
      </button>
    </div>

    <!-- Filter bar -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <div class="relative">
        <input
          v-model="searchInput"
          type="search"
          :placeholder="__('Search leads...')"
          :aria-label="__('Search leads')"
          class="w-64 rounded-md border border-gray-300 py-1.5 pl-3 pr-8 text-sm text-gray-700 placeholder:text-gray-400"
          @keyup.escape="clearSearch"
        />
        <button
          v-if="searchInput"
          type="button"
          class="absolute inset-y-0 right-0 px-2 text-gray-400 hover:text-gray-900"
          :title="__('Clear search')"
          :aria-label="__('Clear search')"
          @click="clearSearch"
        >
          &times;
        </button>
      </div>

      <select
        v-model="source"
        class="rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
      >
        <option value="">{{ __('All sources') }}</option>
        <option v-for="s in MICRO_SOURCES" :key="s" :value="s">{{ __(s) }}</option>
      </select>

      <select
        v-model="priority"
        class="rounded-md border border-gray-300 px-2 py-1.5 text-sm text-gray-700"
      >
        <option value="">{{ __('Any priority') }}</option>
        <option value="High">{{ __('High') }}</option>
        <option value="Medium">{{ __('Medium') }}</option>
        <option value="Low">{{ __('Low') }}</option>
      </select>

      <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-600">
        <input
          v-model="dueOnly"
          type="checkbox"
          class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
        />
        <FieldLabel field="due_only" :label="__('Due today')" :uppercase="false" />
      </label>

      <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-600">
        <input
          v-model="showClosed"
          type="checkbox"
          class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
        />
        <FieldLabel field="show_closed" :label="__('Show closed stages')" :uppercase="false" />
      </label>

      <button
        v-if="hasFilters"
        type="button"
        class="text-sm text-gray-500 underline hover:text-gray-900"
        @click="clearFilters"
      >
        {{ __('Clear filters') }}
      </button>
    </div>

    <!-- No search hits -->
    <div
      v-if="searchFoundNothing"
      class="mb-4 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-600"
    >
      {{ __('No leads match "{term}".', { term: search }) }}
      <span v-if="!showClosed">
        {{ __('Won and lost leads sit in closed stages — tick "Show closed stages" to search those too.') }}
      </span>
    </div>

    <!-- Loading -->
    <div v-if="pipeline.loading && !pipeline.data" class="flex flex-1 items-center justify-center">
      <p class="text-sm text-gray-500">{{ __('Loading...') }}</p>
    </div>

    <!-- Error -->
    <div v-else-if="pipeline.error" class="flex flex-1 items-center justify-center">
      <p class="text-sm text-red-500">{{ __('Failed to load pipeline. Please try again.') }}</p>
    </div>

    <!-- No pipeline configured -->
    <div v-else-if="!activePipeline" class="flex flex-1 flex-col items-center justify-center gap-2">
      <p class="text-sm text-gray-500">{{ __('No pipeline configured') }}</p>
      <button
        type="button"
        class="text-sm font-medium text-gray-900 hover:text-gray-700"
        @click="startCreate"
      >
        {{ __('Create pipeline') }} &rarr;
      </button>
    </div>

    <!-- Kanban Board -->
    <div v-else class="flex flex-1 gap-4 overflow-x-auto pb-4">
      <!-- Leads without a stage -->
      <div
        v-if="pipeline.data?.unassigned?.length"
        class="flex w-72 shrink-0 flex-col rounded-lg border-t-4 border-gray-300 bg-gray-50"
      >
        <div class="flex items-center justify-between px-3 py-2.5">
          <h3 class="text-sm font-semibold text-gray-500">
            {{ __('Unassigned') }}
          </h3>
          <span
            class="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-gray-100 px-1.5 text-[10px] font-medium text-gray-600"
          >
            {{ pipeline.data.unassigned.length }}
          </span>
        </div>
        <div class="flex min-h-[100px] flex-1 flex-col gap-2 overflow-y-auto overflow-x-hidden px-2 pb-2">
          <router-link
            v-for="lead in pipeline.data.unassigned"
            :key="lead.name"
            :to="`/micro/leads/${lead.name}`"
            class="min-w-0 rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow-md"
          >
            <p
              class="line-clamp-2 break-words text-sm font-medium text-gray-900"
              :title="lead.lead_name"
            >
              {{ lead.lead_name }}
            </p>
          </router-link>
        </div>
      </div>

      <!-- Stage columns -->
      <KanbanColumn
        v-for="col in pipeline.data?.stages"
        :key="col.stage.name"
        :stage="col.stage"
        :leads="col.leads"
        :count="col.count"
        :value="col.value"
        @drop="onDrop"
        @add="startAddLead(col.stage.name, col.stage.stage_name)"
      />

      <!-- Empty state -->
      <div
        v-if="!pipeline.data?.stages?.length"
        class="flex flex-1 flex-col items-center justify-center gap-2"
      >
        <p class="text-sm text-gray-500">{{ __('No pipeline stages configured') }}</p>
        <button
          type="button"
          class="text-sm font-medium text-gray-900 hover:text-gray-700"
          @click="managing = activePipeline"
        >
          {{ __('Add stage') }} &rarr;
        </button>
      </div>
    </div>

    <!-- New pipeline dialog -->
    <Teleport to="body">
      <div
        v-if="creating"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
        @click.self="creating = false"
      >
        <div class="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl">
          <h2 class="text-base font-semibold text-gray-900">{{ __('New pipeline') }}</h2>
          <p class="mt-1 text-xs text-gray-500">
            {{ __('One pipeline per repeatable process — different stages mean a different pipeline.') }}
          </p>
          <input
            v-model="newPipelineName"
            type="text"
            :placeholder="__('Pipeline Name')"
            class="mt-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            @keyup.enter="onCreatePipeline"
          />
          <p v-if="createError" class="mt-2 text-xs text-red-600">{{ createError }}</p>
          <div class="mt-4 flex justify-end gap-2">
            <button
              type="button"
              class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              @click="creating = false"
            >
              {{ __('Cancel') }}
            </button>
            <button
              type="button"
              class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
              @click="onCreatePipeline"
            >
              {{ __('Create') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- New lead dialog -->
    <LeadDialog
      v-if="addingLead && activePipeline"
      :pipeline="activePipeline"
      :stage="addingLead.stage || undefined"
      :stage-name="addingLead.stageName || undefined"
      @close="addingLead = null"
      @created="onLeadCreated"
    />

    <!-- Pipeline management dialog -->
    <PipelineManager
      v-if="managing"
      :pipeline="managing"
      @close="managing = ''"
      @changed="onPipelineChanged"
      @deleted="onPipelineDeleted"
    />
  </div>
</template>
