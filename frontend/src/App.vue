<!--
  SPDX-License-Identifier: AGPL-3.0-or-later
  Copyright (C) 2026 Tonic
-->
<script setup lang="ts">
// @ts-ignore — served by Dock's built assets
import { DockLayout, DockSidebarShell } from '/assets/dock/js/dock-navbar.esm.js'
import {
  LayoutDashboard, Users, Columns3, HeartPulse,
  Package, FileText, FileMinus, Receipt,
  Download,
} from 'lucide-vue-next'
import { __ } from '@/composables/useTranslate'

const navItems = [
  { key: 'dashboard',      label: __('Dashboard'),      icon: LayoutDashboard, path: '/micro',                exact: true },
  // CRM
  { key: 'customers',      label: __('Customers'),      icon: Users,       path: '/micro/customers',      divider: true },
  { key: 'pipeline',       label: __('Pipeline'),       icon: Columns3,    path: '/micro/pipeline' },
  { key: 'portfolio',      label: __('Client Portfolio'), icon: HeartPulse, path: '/micro/portfolio' },
  // Documents
  { key: 'articles',       label: __('Articles'),       icon: Package,     path: '/micro/articles',       divider: true },
  { key: 'offers',         label: __('Offer Drafts'),   icon: FileText,    path: '/micro/offers' },
  { key: 'invoice-drafts', label: __('Invoice Drafts'), icon: FileMinus,   path: '/micro/invoice-drafts' },
  { key: 'receipts',       label: __('Receipts'),       icon: Receipt,     path: '/micro/receipts' },
  // Tools
  { key: 'export',         label: __('Export'),         icon: Download,    path: '/micro/export',         divider: true },
]

declare const __APP_VERSION__: string

const footer = {
  edition: __('Community Edition'),
  version: __APP_VERSION__,
  sourceUrl: 'https://github.com/tonic-6101/micro',
}
</script>

<template>
  <DockLayout>
    <DockSidebarShell
      color="#2563eb"
      :items="navItems"
      :footer="footer"
      aria-label="Micro navigation"
    />
    <main class="flex flex-1 flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
      <div class="flex-1 overflow-auto p-6">
        <router-view />
      </div>
    </main>
  </DockLayout>
</template>
