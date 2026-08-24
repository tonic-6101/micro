<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { MicroColor, PipelineSetupResponse, PipelineSetupStage } from '@/types/micro'

const props = defineProps<{
  pipeline: string
}>()

const emit = defineEmits<{
  close: []
  changed: [pipeline: string]
  deleted: []
}>()

const COLORS: MicroColor[] = ['Gray', 'Blue', 'Green', 'Yellow', 'Orange', 'Red', 'Purple', 'Pink']

const swatch: Record<string, string> = {
  Gray: 'bg-gray-400',
  Blue: 'bg-blue-500',
  Green: 'bg-green-500',
  Yellow: 'bg-yellow-500',
  Orange: 'bg-orange-500',
  Red: 'bg-red-500',
  Purple: 'bg-purple-500',
  Pink: 'bg-pink-500',
}

const name = ref('')
const segment = ref('')
const description = ref('')
const isDefault = ref(false)
const isActive = ref(true)
const stages = ref<PipelineSetupStage[]>([])
const newStageName = ref('')
const confirmDelete = ref(false)
const errorMessage = ref('')
const pendingStageDeletion = ref<PipelineSetupStage | null>(null)
const moveLeadsTo = ref('')

const setup = createResource({
  url: 'micro.api.pipeline_admin.get_pipeline_setup',
  transform(data: PipelineSetupResponse) {
    return data
  },
  onSuccess(data: PipelineSetupResponse) {
    name.value = data.pipeline.pipeline_name
    segment.value = data.pipeline.segment || ''
    description.value = data.pipeline.description || ''
    isDefault.value = Boolean(data.pipeline.is_default)
    isActive.value = Boolean(data.pipeline.is_active)
    stages.value = [...data.stages]
  },
})

const segments = createResource({
  url: 'micro.api.pipeline.get_segments',
  auto: true,
})

const savePipeline = createResource({ url: 'micro.api.pipeline_admin.update_pipeline' })
const removePipeline = createResource({ url: 'micro.api.pipeline_admin.delete_pipeline' })
const addStage = createResource({ url: 'micro.api.pipeline_admin.create_stage' })
const saveStage = createResource({ url: 'micro.api.pipeline_admin.update_stage' })
const removeStage = createResource({ url: 'micro.api.pipeline_admin.delete_stage' })
const persistOrder = createResource({ url: 'micro.api.pipeline_admin.reorder_stages' })

const leadCount = computed(() => setup.data?.lead_count ?? 0)

const moveTargets = computed(() =>
  stages.value.filter((stage) => stage.name !== pendingStageDeletion.value?.name),
)

watch(
  () => props.pipeline,
  (value) => {
    if (value) {
      errorMessage.value = ''
      confirmDelete.value = false
      setup.update({ params: { pipeline: value } })
      setup.reload()
    }
  },
  { immediate: true },
)

function reload() {
  setup.reload()
}

function fail(error: unknown) {
  errorMessage.value = (error as { messages?: string[] })?.messages?.[0] || String(error)
}

function onSavePipeline() {
  errorMessage.value = ''
  savePipeline
    .submit({
      pipeline: props.pipeline,
      pipeline_name: name.value,
      segment: segment.value,
      description: description.value,
      is_default: isDefault.value ? 1 : 0,
      is_active: isActive.value ? 1 : 0,
    })
    .then((result: { pipeline: string }) => {
      emit('changed', result.pipeline)
      emit('close')
    })
    .catch(fail)
}

function onAddStage() {
  const stageName = newStageName.value.trim()
  if (!stageName) return
  errorMessage.value = ''
  addStage
    .submit({ pipeline: props.pipeline, stage_name: stageName, color: 'Gray', outcome: 'open' })
    .then(() => {
      newStageName.value = ''
      reload()
    })
    .catch(fail)
}

function onStageChange(stage: PipelineSetupStage) {
  errorMessage.value = ''
  saveStage
    .submit({
      stage: stage.name,
      stage_name: stage.stage_name,
      color: stage.color,
      outcome: stage.outcome,
    })
    .then(reload)
    .catch(fail)
}

function move(index: number, delta: number) {
  const target = index + delta
  if (target < 0 || target >= stages.value.length) return
  const next = [...stages.value]
  const [moved] = next.splice(index, 1)
  next.splice(target, 0, moved)
  stages.value = next
  persistOrder
    .submit({ pipeline: props.pipeline, stage_ids: next.map((s) => s.name) })
    .catch(fail)
}

function askDeleteStage(stage: PipelineSetupStage) {
  errorMessage.value = ''
  if (!stage.lead_count) {
    removeStage.submit({ stage: stage.name }).then(reload).catch(fail)
    return
  }
  pendingStageDeletion.value = stage
  moveLeadsTo.value = moveTargets.value[0]?.name || ''
}

function confirmDeleteStage() {
  if (!pendingStageDeletion.value) return
  removeStage
    .submit({ stage: pendingStageDeletion.value.name, move_leads_to: moveLeadsTo.value })
    .then(() => {
      pendingStageDeletion.value = null
      reload()
    })
    .catch(fail)
}

function onDeletePipeline() {
  errorMessage.value = ''
  removePipeline
    .submit({ pipeline: props.pipeline })
    .then(() => emit('deleted'))
    .catch(fail)
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      @click.self="emit('close')"
    >
      <div class="flex max-h-[90vh] w-full max-w-2xl flex-col overflow-hidden rounded-xl bg-white shadow-xl">
        <!-- Header -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <h2 class="text-base font-semibold text-gray-900">{{ __('Edit Pipeline') }}</h2>
          <button
            type="button"
            class="rounded-md px-2 py-1 text-sm text-gray-500 hover:bg-gray-100"
            @click="emit('close')"
          >
            &times;
          </button>
        </div>

        <div class="flex-1 space-y-5 overflow-auto px-5 py-4">
          <p v-if="errorMessage" class="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {{ errorMessage }}
          </p>

          <!-- Pipeline fields -->
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="block">
              <span class="text-xs font-medium text-gray-600">{{ __('Pipeline Name') }}</span>
              <input
                v-model="name"
                type="text"
                class="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </label>

            <label class="block">
              <span class="text-xs font-medium text-gray-600">{{ __('Segment') }}</span>
              <select
                v-model="segment"
                class="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">{{ __('No segment') }}</option>
                <option v-for="s in segments.data?.segments || []" :key="s.name" :value="s.name">
                  {{ s.segment_name }}
                </option>
              </select>
            </label>
          </div>

          <label class="block">
            <span class="text-xs font-medium text-gray-600">{{ __('Description') }}</span>
            <input
              v-model="description"
              type="text"
              class="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>

          <div class="flex flex-wrap gap-4">
            <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
              <input
                v-model="isDefault"
                type="checkbox"
                class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
              />
              {{ __('Open this pipeline by default') }}
            </label>
            <label class="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
              <input
                v-model="isActive"
                type="checkbox"
                class="rounded border-gray-300 text-gray-900 focus:ring-gray-500"
              />
              {{ __('Show in the tab bar') }}
            </label>
          </div>

          <!-- Stages -->
          <div>
            <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
              {{ __('Stages') }}
            </h3>

            <div class="space-y-2">
              <div
                v-for="(stage, index) in stages"
                :key="stage.name"
                class="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 px-2 py-2"
              >
                <div class="flex flex-col">
                  <button
                    type="button"
                    class="px-1 text-xs text-gray-400 hover:text-gray-900 disabled:opacity-30"
                    :disabled="index === 0"
                    @click="move(index, -1)"
                  >
                    &uarr;
                  </button>
                  <button
                    type="button"
                    class="px-1 text-xs text-gray-400 hover:text-gray-900 disabled:opacity-30"
                    :disabled="index === stages.length - 1"
                    @click="move(index, 1)"
                  >
                    &darr;
                  </button>
                </div>

                <span class="h-3 w-3 shrink-0 rounded-full" :class="swatch[stage.color || 'Gray']" />

                <input
                  v-model="stage.stage_name"
                  type="text"
                  class="min-w-0 flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm"
                  @blur="onStageChange(stage)"
                />

                <select
                  v-model="stage.color"
                  class="rounded-md border border-gray-300 px-1.5 py-1 text-xs"
                  @change="onStageChange(stage)"
                >
                  <option v-for="c in COLORS" :key="c" :value="c">{{ __(c) }}</option>
                </select>

                <select
                  v-model="stage.outcome"
                  class="rounded-md border border-gray-300 px-1.5 py-1 text-xs"
                  @change="onStageChange(stage)"
                >
                  <option value="open">{{ __('Open') }}</option>
                  <option value="win">{{ __('Won') }}</option>
                  <option value="loss">{{ __('Lost') }}</option>
                </select>

                <span class="w-14 text-right text-[11px] text-gray-400">
                  {{ stage.lead_count }} {{ __('leads') }}
                </span>

                <button
                  type="button"
                  class="rounded-md px-2 py-1 text-xs text-gray-400 hover:bg-red-50 hover:text-red-700"
                  @click="askDeleteStage(stage)"
                >
                  {{ __('Delete') }}
                </button>
              </div>
            </div>

            <!-- Move-leads confirmation -->
            <div
              v-if="pendingStageDeletion"
              class="mt-2 rounded-lg border border-orange-200 bg-orange-50 p-3"
            >
              <p class="text-sm text-orange-900">
                {{ pendingStageDeletion.lead_count }}
                {{ __('leads are in this stage. Move them to:') }}
              </p>
              <div class="mt-2 flex flex-wrap items-center gap-2">
                <select
                  v-model="moveLeadsTo"
                  class="rounded-md border border-gray-300 px-2 py-1 text-sm"
                >
                  <option v-for="s in moveTargets" :key="s.name" :value="s.name">
                    {{ s.stage_name }}
                  </option>
                </select>
                <button
                  type="button"
                  class="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-800"
                  @click="confirmDeleteStage"
                >
                  {{ __('Move and delete') }}
                </button>
                <button
                  type="button"
                  class="text-sm text-gray-500 underline"
                  @click="pendingStageDeletion = null"
                >
                  {{ __('Cancel') }}
                </button>
              </div>
            </div>

            <!-- Add stage -->
            <div class="mt-3 flex items-center gap-2">
              <input
                v-model="newStageName"
                type="text"
                :placeholder="__('New stage name')"
                class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                @keyup.enter="onAddStage"
              />
              <button
                type="button"
                class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                @click="onAddStage"
              >
                {{ __('Add stage') }}
              </button>
            </div>
          </div>

          <!-- Danger zone -->
          <div class="rounded-lg border border-gray-200 p-3">
            <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500">
              {{ __('Delete pipeline') }}
            </h3>
            <p class="mt-1 text-xs text-gray-500">
              <span v-if="leadCount">
                {{ leadCount }}
                {{ __('leads are still in this pipeline — uncheck "Show in the tab bar" to hide it without losing history.') }}
              </span>
              <span v-else>{{ __('This pipeline has no leads and can be removed.') }}</span>
            </p>
            <div class="mt-2 flex items-center gap-2">
              <button
                v-if="!confirmDelete"
                type="button"
                class="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-40"
                :disabled="Boolean(leadCount)"
                @click="confirmDelete = true"
              >
                {{ __('Delete pipeline') }}
              </button>
              <template v-else>
                <button
                  type="button"
                  class="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
                  @click="onDeletePipeline"
                >
                  {{ __('Yes, delete permanently') }}
                </button>
                <button
                  type="button"
                  class="text-sm text-gray-500 underline"
                  @click="confirmDelete = false"
                >
                  {{ __('Cancel') }}
                </button>
              </template>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button
            type="button"
            class="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            @click="emit('close')"
          >
            {{ __('Cancel') }}
          </button>
          <button
            type="button"
            class="rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800"
            @click="onSavePipeline"
          >
            {{ __('Save') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
