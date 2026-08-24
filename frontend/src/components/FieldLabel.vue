<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<!--
  A field label that explains itself on hover.

  Ecosystem rule: no labelled point stands alone. Pass the fieldname and the
  wording comes from `glossary.ts`, so the same field reads the same way on
  every page.

  The label *is* the target — there is no help mark to aim for. A mark on every
  row is clutter on a form that has twelve of them, and it teaches a rule the
  user then has to remember; hovering the thing you are wondering about needs
  no teaching. The pointer turning into a question mark is the whole hint.
-->
<script setup lang="ts">
import { computed } from 'vue'
import { hintFor } from '@/glossary'

const props = withDefaults(
  defineProps<{
    /** The label text. Omit it and pass the default slot instead — a status
        pill or a checkbox caption is a point that needs explaining too. */
    label?: string
    /** Fieldname — looks the explanation up in the glossary. */
    field?: string
    /** Explanation written on the spot, for labels that are not a field. */
    hint?: string
    uppercase?: boolean
    /** Which edge the bubble hangs from — `right` for labels near the right margin. */
    align?: 'left' | 'right'
  }>(),
  { uppercase: true, align: 'left' },
)

const text = computed(() => props.hint || hintFor(props.field))

// Tying the bubble to its label by id is what lets a screen reader read the
// explanation out; without the mark, the label itself carries that job.
const tooltipId = `field-hint-${Math.random().toString(36).slice(2, 10)}`
</script>

<template>
  <span
    class="group relative inline-flex items-center text-xs text-gray-500"
    :class="[uppercase ? 'uppercase' : 'font-medium', text ? 'cursor-help' : '']"
    :tabindex="text ? 0 : undefined"
    :aria-describedby="text ? tooltipId : undefined"
  >
    <slot>{{ label }}</slot>

    <span
      v-if="text"
      :id="tooltipId"
      role="tooltip"
      class="pointer-events-none absolute top-full z-30 mt-1 hidden w-64 max-w-[80vw] rounded-md bg-gray-900 px-2.5 py-2 text-xs font-normal normal-case leading-snug text-white shadow-lg group-hover:block group-focus-visible:block"
      :class="align === 'right' ? 'right-0' : 'left-0'"
    >
      {{ text }}
    </span>
  </span>
</template>
