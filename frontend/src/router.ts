// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
// @ts-ignore — served by Dock's built assets
import { dockSharedRoutes } from '/assets/dock/js/dock-navbar.esm.js'

const routes: RouteRecordRaw[] = [
  {
    path: '/micro',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/micro/customers',
    name: 'Customers',
    component: () => import('@/pages/Customers.vue'),
  },
  {
    path: '/micro/customers/new',
    name: 'CustomerNew',
    component: () => import('@/pages/CustomerNew.vue'),
  },
  {
    path: '/micro/customers/:id',
    name: 'CustomerDetail',
    component: () => import('@/pages/CustomerDetail.vue'),
    props: true,
  },
  {
    path: '/micro/pipeline',
    name: 'Pipeline',
    component: () => import('@/pages/Pipeline.vue'),
  },
  {
    path: '/micro/articles',
    name: 'Articles',
    component: () => import('@/pages/Articles.vue'),
  },
  {
    path: '/micro/offers',
    name: 'Offers',
    component: () => import('@/pages/Offers.vue'),
  },
  {
    path: '/micro/offers/:id',
    name: 'OfferDetail',
    component: () => import('@/pages/OfferDetail.vue'),
    props: true,
  },
  {
    path: '/micro/invoice-drafts',
    name: 'InvoiceDrafts',
    component: () => import('@/pages/InvoiceDrafts.vue'),
  },
  {
    path: '/micro/invoice-drafts/:id',
    name: 'InvoiceDraftDetail',
    component: () => import('@/pages/InvoiceDraftDetail.vue'),
    props: true,
  },
  {
    path: '/micro/receipts',
    name: 'Receipts',
    component: () => import('@/pages/Receipts.vue'),
  },
  {
    path: '/micro/export',
    name: 'Export',
    component: () => import('@/pages/Export.vue'),
  },
  // Dock shared pages (Calendar, People, Notifications, Notes, Bookmarks, Activity, Discussions)
  ...dockSharedRoutes('/micro'),
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
