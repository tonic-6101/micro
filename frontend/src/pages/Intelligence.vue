<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2024-2026 Tonic
-->
<script setup lang="ts">
import { createResource } from 'frappe-ui'
import { __ } from '@/composables/useTranslate'

const briefing = createResource({
  url: 'micro.api.intelligence.get_weekly_briefing',
  auto: true,
})

const nudges = createResource({
  url: 'micro.api.intelligence.get_nudges',
  auto: true,
})

const winRate = createResource({
  url: 'micro.api.intelligence.get_win_rate',
  auto: true,
})

const runway = createResource({
  url: 'micro.api.intelligence.get_revenue_runway',
  auto: true,
})
</script>

<template>
  <div class="p-6 space-y-8">
    <h1 class="text-xl font-semibold text-gray-900">{{ __('Business Intelligence') }}</h1>

    <!-- Weekly Briefing -->
    <section v-if="briefing.data" class="rounded-lg border border-gray-200 p-5">
      <h2 class="text-sm font-semibold text-gray-500 uppercase mb-4">{{ __('Weekly Briefing') }}</h2>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ briefing.data.pipeline?.open_leads ?? 0 }}</div>
          <div class="text-xs text-gray-500">{{ __('Open Leads') }}</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-amber-600">{{ briefing.data.offers?.pending ?? 0 }}</div>
          <div class="text-xs text-gray-500">{{ __('Offers Pending') }}</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-gray-700">{{ briefing.data.invoices?.pending ?? 0 }}</div>
          <div class="text-xs text-gray-500">{{ __('Invoice Drafts') }}</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ briefing.data.pipeline?.won_this_week ?? 0 }}</div>
          <div class="text-xs text-gray-500">{{ __('Won This Week') }}</div>
        </div>
      </div>

      <!-- Suggested Action -->
      <div
        v-if="briefing.data.suggested_action"
        class="rounded-md p-3 text-sm"
        :class="{
          'bg-red-50 text-red-800': briefing.data.suggested_action.priority === 'high',
          'bg-amber-50 text-amber-800': briefing.data.suggested_action.priority === 'medium',
          'bg-green-50 text-green-800': briefing.data.suggested_action.priority === 'low',
        }"
      >
        {{ briefing.data.suggested_action.message }}
      </div>
    </section>

    <!-- Follow-Up Nudges -->
    <section v-if="nudges.data" class="rounded-lg border border-gray-200 p-5">
      <h2 class="text-sm font-semibold text-gray-500 uppercase mb-4">{{ __('Follow-Up Nudges') }}</h2>

      <div v-if="nudges.data.unanswered_offers?.length" class="mb-4">
        <h3 class="text-xs font-medium text-amber-700 mb-2">{{ __('Unanswered Offers') }}</h3>
        <div v-for="offer in nudges.data.unanswered_offers" :key="offer.name" class="flex justify-between py-1.5 text-sm border-b border-gray-100 last:border-0">
          <span>{{ offer.reference }} &mdash; {{ offer.contact }}</span>
          <span class="text-amber-600">{{ offer.days_waiting }}d</span>
        </div>
      </div>

      <div v-if="nudges.data.dormant_contacts?.length" class="mb-4">
        <h3 class="text-xs font-medium text-gray-600 mb-2">{{ __('Dormant Contacts') }}</h3>
        <div v-for="c in nudges.data.dormant_contacts" :key="c.name" class="flex justify-between py-1.5 text-sm border-b border-gray-100 last:border-0">
          <span>{{ c.full_name || c.name }}</span>
          <span class="text-gray-400">{{ c.days_inactive }}d {{ __('inactive') }}</span>
        </div>
      </div>

      <div v-if="nudges.data.upcoming_follow_ups?.length">
        <h3 class="text-xs font-medium text-blue-700 mb-2">{{ __('Upcoming Follow-Ups') }}</h3>
        <div v-for="lead in nudges.data.upcoming_follow_ups" :key="lead.name" class="flex justify-between py-1.5 text-sm border-b border-gray-100 last:border-0">
          <span>{{ lead.lead_name }}</span>
          <span class="text-blue-600">{{ lead.days_until === 0 ? __('Today') : lead.days_until + 'd' }}</span>
        </div>
      </div>

      <div v-if="!nudges.data.unanswered_offers?.length && !nudges.data.dormant_contacts?.length && !nudges.data.upcoming_follow_ups?.length" class="text-sm text-gray-400 text-center py-4">
        {{ __('No nudges right now. You\'re on top of things!') }}
      </div>
    </section>

    <!-- Win Rate -->
    <section v-if="winRate.data" class="rounded-lg border border-gray-200 p-5">
      <h2 class="text-sm font-semibold text-gray-500 uppercase mb-4">{{ __('Win Rate') }}</h2>

      <div class="flex items-baseline gap-4 mb-3">
        <span class="text-3xl font-bold" :class="winRate.data.has_enough_data ? 'text-gray-900' : 'text-gray-400'">
          {{ winRate.data.win_rate }}%
        </span>
        <span class="text-sm text-gray-500">
          {{ winRate.data.accepted }} {{ __('won') }} / {{ winRate.data.resolved }} {{ __('resolved') }}
        </span>
      </div>

      <div v-if="!winRate.data.has_enough_data" class="text-xs text-gray-400">
        {{ __('Need 10+ resolved offers for reliable insights. Currently at') }} {{ winRate.data.resolved }}.
      </div>

      <div v-if="winRate.data.monthly_trend?.length" class="mt-4 flex gap-1 items-end h-16">
        <div
          v-for="m in winRate.data.monthly_trend"
          :key="m.month"
          class="flex-1 bg-blue-200 rounded-t"
          :style="{ height: m.win_rate + '%', minHeight: m.resolved > 0 ? '4px' : '1px' }"
          :title="m.label + ': ' + m.win_rate + '%'"
        ></div>
      </div>
    </section>

    <!-- Revenue Runway -->
    <section v-if="runway.data" class="rounded-lg border border-gray-200 p-5">
      <h2 class="text-sm font-semibold text-gray-500 uppercase mb-4">{{ __('Revenue Runway') }}</h2>

      <div class="grid grid-cols-3 gap-4 mb-4">
        <div class="text-center">
          <div class="text-lg font-bold text-green-600">{{ runway.data.confirmed_weeks }}w</div>
          <div class="text-xs text-gray-500">{{ __('Confirmed') }}</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-bold text-amber-500">{{ runway.data.pipeline_weeks }}w</div>
          <div class="text-xs text-gray-500">{{ __('Pipeline (50%)') }}</div>
        </div>
        <div class="text-center">
          <div class="text-lg font-bold text-gray-900">{{ runway.data.total_runway_weeks }}w</div>
          <div class="text-xs text-gray-500">{{ __('Total Runway') }}</div>
        </div>
      </div>

      <!-- Runway bar -->
      <div class="h-3 bg-gray-100 rounded-full overflow-hidden flex">
        <div
          class="bg-green-500 h-full"
          :style="{ width: (runway.data.total_runway_weeks > 0 ? runway.data.confirmed_weeks / runway.data.total_runway_weeks * 100 : 0) + '%' }"
        ></div>
        <div
          class="bg-amber-400 h-full"
          :style="{ width: (runway.data.total_runway_weeks > 0 ? runway.data.pipeline_weeks / runway.data.total_runway_weeks * 100 : 0) + '%' }"
        ></div>
      </div>
    </section>
  </div>
</template>
