// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

/** Micro Customer DocType */
export interface MicroCustomer {
  name: string
  name1: string
  last_name?: string
  full_name: string
  contact_type: 'Person' | 'Organization'
  status: 'Potential' | 'Active' | 'Inactive'
  organization?: string
  email?: string
  phone?: string
  mobile?: string
  website?: string
  source?: 'Manual' | 'Google Ads' | 'Facebook' | 'Instagram' | 'LinkedIn' | 'Email Campaign' | 'Cold Call' | 'Web Form' | 'Organic Search' | 'Referral' | 'Partner' | 'Event' | 'Import' | 'Other'
  pipeline_stage?: string
  address?: string
  city?: string
  postal_code?: string
  country?: string
  notes?: string
  image?: string
  modified?: string
  creation?: string
}

/** Micro Task DocType */
export interface MicroTask {
  name: string
  title: string
  status: 'Open' | 'In Progress' | 'Completed' | 'Cancelled'
  priority?: 'Low' | 'Medium' | 'High'
  due_date?: string
  contact?: string
  description?: string
  modified?: string
  creation?: string
}

/** Micro Note DocType */
export interface MicroNote {
  name: string
  note_type: 'Note' | 'Call' | 'Meeting' | 'Email Summary'
  content: string
  contact?: string
  modified?: string
  creation?: string
}

/** Micro Pipeline Stage DocType */
export interface MicroPipelineStage {
  name: string
  stage_name: string
  sort_order: number
  color?: 'Gray' | 'Blue' | 'Green' | 'Yellow' | 'Orange' | 'Red' | 'Purple' | 'Pink'
  is_closed: boolean
}

/** Pipeline column: a stage with its grouped customers */
export interface PipelineColumn {
  stage: MicroPipelineStage
  customers: MicroCustomer[]
}

/** API response: pipeline Kanban data */
export interface PipelineResponse {
  stages: PipelineColumn[]
  unassigned: MicroCustomer[]
}

/** API response: stages list */
export interface StagesListResponse {
  stages: MicroPipelineStage[]
}

/** API response: customers list */
export interface CustomersListResponse {
  customers: MicroCustomer[]
  total: number
}

/** API response: single customer with related data */
export interface CustomerDetailResponse {
  customer: MicroCustomer
  notes: MicroNote[]
  tasks: MicroTask[]
}

/** Micro Article DocType (Zone 2) */
export interface MicroArticle {
  name: string
  article_name: string
  article_code?: string
  category?: string
  unit?: string
  is_active?: boolean
  selling_price: number
  purchase_price?: number
  description?: string
  supplier?: string
  notes?: string
  image?: string
  modified?: string
  creation?: string
}

/** Micro Offer Item (child table, Zone 2) */
export interface MicroOfferItem {
  name: string
  article?: string
  description: string
  quantity: number
  unit?: string
  rate: number
  amount: number
}

/** Micro Offer Draft DocType (Zone 2) */
export interface MicroOfferDraft {
  name: string
  reference: string
  title?: string
  contact: string
  date: string
  valid_until?: string
  status: 'Draft' | 'Sent' | 'Accepted' | 'Declined' | 'Expired'
  language?: string
  items: MicroOfferItem[]
  total: number
  notes?: string
  internal_notes?: string
  is_draft: boolean
  watermark_text: string
  disclaimer: string
  modified?: string
  creation?: string
}

/** API response: articles list */
export interface ArticlesListResponse {
  articles: MicroArticle[]
  total: number
}

/** API response: single article */
export interface ArticleDetailResponse {
  article: MicroArticle
}

/** API response: offers list */
export interface OffersListResponse {
  offers: MicroOfferDraft[]
  total: number
}

/** API response: single offer */
export interface OfferDetailResponse {
  offer: MicroOfferDraft
}

/** Micro Invoice Item (child table, Zone 2) */
export interface MicroInvoiceItem {
  name: string
  article?: string
  description: string
  quantity: number
  unit?: string
  rate: number
  amount: number
}

/** Micro Invoice Draft DocType (Zone 2) */
export interface MicroInvoiceDraft {
  name: string
  reference: string
  title?: string
  contact: string
  date: string
  status: 'Draft' | 'Sent to Tax Advisor' | 'Archived'
  language?: string
  source: 'Manual' | 'From Offer' | 'From Time Entries'
  offer_draft?: string
  items: MicroInvoiceItem[]
  total: number
  notes?: string
  internal_notes?: string
  is_draft: boolean
  watermark_text: string
  disclaimer: string
  modified?: string
  creation?: string
}

/** Micro Receipt DocType (Zone 2) */
export interface MicroReceipt {
  name: string
  receipt_date: string
  vendor?: string
  amount: number
  category: 'Materials' | 'Travel' | 'Office' | 'Food' | 'Software' | 'Services' | 'Other'
  description?: string
  image?: string
  contact?: string
  notes?: string
  exported: boolean
  export_date?: string
  modified?: string
  creation?: string
}

/** API response: invoices list */
export interface InvoicesListResponse {
  invoices: MicroInvoiceDraft[]
  total: number
}

/** API response: single invoice */
export interface InvoiceDetailResponse {
  invoice: MicroInvoiceDraft
}

/** API response: receipts list */
export interface ReceiptsListResponse {
  receipts: MicroReceipt[]
  total: number
}

/** API response: single receipt */
export interface ReceiptDetailResponse {
  receipt: MicroReceipt
}

/** Dashboard KPI response */
export interface DashboardKPIs {
  customers: { total: number; by_status: Record<string, number>; by_source: Record<string, number> }
  tasks: { open: number }
  offers: { total: number; by_status: Record<string, number> }
  invoices: { total: number; by_status: Record<string, number> }
  receipts: {
    total: number
    unexported: number
    by_category: Record<string, number>
    total_amount: number
  }
  recent_activity: Array<{
    doctype: string
    name: string
    label: string
    modified: string
  }>
}

/** Export preview response */
export interface ExportPreviewResponse {
  doc_type: string
  count: number
  filters: Record<string, unknown>
}

/** Export CSV response */
export interface ExportCsvResponse {
  csv: string
  count: number
  filename: string
  marked_exported?: number
}

/** Micro Settings (Single DocType) */
export interface MicroSettings {
  company_name: string
  company_email?: string
  company_phone?: string
  company_address?: string
  company_logo?: string
  default_currency: string
  default_language: string
  customer_limit: number
  article_limit: number
  draft_watermark_text: string
  draft_disclaimer?: string
  tax_advisor_name?: string
  tax_advisor_email?: string
  enable_orga_integration: boolean
}
