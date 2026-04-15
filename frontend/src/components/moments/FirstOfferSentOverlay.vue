<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'
import type { FirstOfferSentStatus } from '@/types/micro'

const props = withDefaults(defineProps<{
  force?: boolean
}>(), { force: false })

const emit = defineEmits<{
  dismiss: []
}>()

const visible = ref(false)

const status = createResource({
  url: 'micro.api.moments.get_first_offer_sent_status',
  params: { force: props.force ? 1 : 0 },
  auto: true,
  transform(data: FirstOfferSentStatus) {
    if (data.should_show) {
      setTimeout(() => { visible.value = true }, 200)
    }
    return data
  },
})

const dismiss = createResource({
  url: 'micro.api.moments.dismiss_first_offer_sent',
  onSuccess() {
    visible.value = false
    emit('dismiss')
  },
})

function handleDismiss() {
  dismiss.submit({})
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="status.data?.should_show && visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
        @click.self="handleDismiss"
      >
        <Transition
          enter-active-class="transition duration-300 ease-out delay-100"
          enter-from-class="opacity-0 translate-y-4 scale-95"
          enter-to-class="opacity-100 translate-y-0 scale-100"
        >
          <div
            v-if="visible"
            class="mx-4 w-full max-w-md rounded-xl bg-white p-8 shadow-xl"
          >
            <h2 class="text-xl font-semibold text-gray-900">
              {{ __('Your first offer is out in the world.') }}
            </h2>

            <p class="mt-4 text-sm leading-relaxed text-gray-600">
              {{ __("That's a real business moment \u2014 someone is reading your offer right now.") }}
            </p>

            <p class="mt-3 text-sm leading-relaxed text-gray-600">
              {{ __("We'll remind you to follow up in 5 days if you haven't heard back. In the meantime, the work is done.") }}
            </p>

            <button
              class="mt-6 inline-flex items-center gap-1 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
              :disabled="dismiss.loading"
              @click="handleDismiss"
            >
              {{ __('Got it') }}
              <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
