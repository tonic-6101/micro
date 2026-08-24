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
    // Ahead of the :id route — a static segment must never read as a contact name.
    path: '/micro/customers/duplicates',
    name: 'Duplicates',
    component: () => import('@/pages/Duplicates.vue'),
  },
  {
    path: '/micro/customers/:id',
    name: 'CustomerDetail',
    component: () => import('@/pages/CustomerDetail.vue'),
    props: true,
  },
  {
    path: '/micro/portfolio',
    name: 'ClientPortfolio',
    component: () => import('@/pages/ClientPortfolio.vue'),
  },
  {
    path: '/micro/pipeline',
    name: 'Pipeline',
    component: () => import('@/pages/Pipeline.vue'),
  },
  {
    path: '/micro/pipeline/:pipelineId',
    name: 'PipelineBoard',
    component: () => import('@/pages/Pipeline.vue'),
    props: true,
  },
  {
    path: '/micro/call-list',
    name: 'CallList',
    component: () => import('@/pages/CallList.vue'),
  },
  {
    path: '/micro/call-list/:pipelineId',
    name: 'CallListPipeline',
    component: () => import('@/pages/CallList.vue'),
    props: true,
  },
  {
    path: '/micro/leads',
    name: 'Leads',
    component: () => import('@/pages/Leads.vue'),
  },
  {
    // Ahead of the :id route — a static segment must never read as a lead name.
    path: '/micro/leads/trash',
    name: 'LeadTrash',
    component: () => import('@/pages/LeadTrash.vue'),
  },
  {
    path: '/micro/leads/:id',
    name: 'LeadDetail',
    component: () => import('@/pages/LeadDetail.vue'),
    props: true,
  },
  {
    path: '/micro/tasks',
    name: 'Tasks',
    component: () => import('@/pages/Tasks.vue'),
  },
  {
    path: '/micro/tasks/:id',
    name: 'TaskDetail',
    component: () => import('@/pages/TaskDetail.vue'),
    props: true,
  },
  {
    path: '/micro/intelligence',
    name: 'Intelligence',
    component: () => import('@/pages/Intelligence.vue'),
  },
  {
    path: '/micro/articles',
    name: 'Articles',
    component: () => import('@/pages/Articles.vue'),
  },
  {
    path: '/micro/articles/new',
    name: 'ArticleNew',
    component: () => import('@/pages/ArticleNew.vue'),
  },
  {
    path: '/micro/articles/:id',
    name: 'ArticleDetail',
    component: () => import('@/pages/ArticleDetail.vue'),
    props: true,
  },
  {
    path: '/micro/offers',
    name: 'Offers',
    component: () => import('@/pages/Offers.vue'),
  },
  {
    path: '/micro/offers/new',
    name: 'OfferNew',
    component: () => import('@/pages/OfferNew.vue'),
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
    path: '/micro/import',
    name: 'Import',
    component: () => import('@/pages/Import.vue'),
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
