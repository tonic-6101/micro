<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
import { ref } from 'vue'
import { __ } from '@/composables/useTranslate'

const sidebarOpen = ref(true)

interface NavItem {
  label: string
  route: string
  icon: string
}

interface NavSection {
  label?: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    items: [
      { label: __('Dashboard'), route: '/micro', icon: 'grid' },
    ],
  },
  {
    label: __('CRM'),
    items: [
      { label: __('Customers'), route: '/micro/customers', icon: 'users' },
      { label: __('Pipeline'), route: '/micro/pipeline', icon: 'columns' },
      { label: __('Tasks'), route: '/micro/tasks', icon: 'check-square' },
    ],
  },
  {
    label: __('Documents'),
    items: [
      { label: __('Articles'), route: '/micro/articles', icon: 'package' },
      { label: __('Offer Drafts'), route: '/micro/offers', icon: 'file-text' },
      { label: __('Invoice Drafts'), route: '/micro/invoice-drafts', icon: 'file-minus' },
      { label: __('Receipts'), route: '/micro/receipts', icon: 'receipt' },
    ],
  },
  {
    label: __('Tools'),
    items: [
      { label: __('Export'), route: '/micro/export', icon: 'download' },
      { label: __('Settings'), route: '/micro/settings', icon: 'settings' },
    ],
  },
]
</script>

<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <aside
      v-if="sidebarOpen"
      class="flex w-56 flex-col border-r border-gray-200 bg-white"
    >
      <!-- Logo -->
      <div class="flex h-14 items-center border-b border-gray-200 px-4">
        <h1 class="text-lg font-semibold text-gray-900">Micro</h1>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-auto px-2 py-3">
        <div v-for="(section, idx) in navSections" :key="idx" class="mb-3">
          <p
            v-if="section.label"
            class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-gray-400"
          >
            {{ section.label }}
          </p>
          <router-link
            v-for="item in section.items"
            :key="item.route"
            :to="item.route"
            class="flex items-center rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            active-class="bg-gray-100 text-gray-900"
          >
            {{ item.label }}
          </router-link>
        </div>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="flex flex-1 flex-col overflow-hidden">
      <!-- Top bar -->
      <header class="flex h-14 items-center border-b border-gray-200 bg-white px-4">
        <button
          class="mr-3 rounded p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          @click="sidebarOpen = !sidebarOpen"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div class="flex-1" />
      </header>

      <!-- Page content -->
      <div class="flex-1 overflow-auto p-6">
        <router-view />
      </div>
    </main>
  </div>
</template>
