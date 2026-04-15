// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

/** Frappe Contact with Micro CRM custom fields */
export interface MicroCustomer {
  name: string
  first_name: string
  last_name?: string
  full_name: string
  micro_contact_type: 'Person' | 'Organization'
  micro_status: 'Potential' | 'Active' | 'Inactive'
  company_name?: string
  email_id?: string
  phone?: string
  mobile_no?: string
  micro_website?: string
  micro_source?: 'Manual' | 'Google Ads' | 'Facebook' | 'Instagram' | 'LinkedIn' | 'Email Campaign' | 'Cold Call' | 'Web Form' | 'Organic Search' | 'Referral' | 'Partner' | 'Event' | 'Import' | 'Other'
  micro_pipeline_stage?: string
  micro_address?: string
  micro_city?: string
  micro_postal_code?: string
  micro_country?: string
  micro_notes?: string
  micro_client_loves?: string
  micro_client_avoid?: string
  micro_communication_style?: 'Email-first' | 'Phone-first' | 'WhatsApp' | 'Async (slow replies OK)' | 'Needs quick responses'
  micro_personal_notes?: string
  micro_opportunities?: string
  micro_last_contact_date?: string
  micro_last_contact_topic?: string
  micro_referred_by?: string
  micro_health_score?: 'A' | 'B' | 'C' | 'D'
  micro_health_score_updated?: string
  image?: string
  modified?: string
  creation?: string
}

/** Micro Note DocType */
export interface MicroNote {
  name: string
  note_type: 'Note' | 'Quick Note' | 'Call' | 'Meeting' | 'Email Summary'
  subject?: string
  date?: string
  content: string
  contact?: string
  is_scope_change?: boolean
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

/** Unified timeline entry from both Micro Notes and Dock Notes */
export interface TimelineNote {
  name: string
  source: 'micro' | 'dock'
  note_type: 'Note' | 'Quick Note' | 'Call' | 'Meeting' | 'Email Summary'
  subject?: string | null
  content: string
  date: string
  modified?: string
  pinned?: boolean
  color?: string
}

/** API response: single customer with related data */
export interface CustomerDetailResponse {
  customer: MicroCustomer
  notes: TimelineNote[]
}

/** Micro Article Category DocType */
export interface MicroArticleCategory {
  name: string
  category_name: string
}

/** Micro Article DocType (Zone 2) */
export interface MicroArticle {
  name: string
  article_name: string
  article_code?: string
  barcode?: string
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

/** Capacity indicator data from micro.api.capacity.get_capacity_data */
export interface CapacityData {
  month_label: string
  capacity_hours: number
  used_hours: number
  available_hours: number
  percentage: number
  raw_percentage: number
  source: 'watch' | 'orga_estimate' | 'none'
  status_key: 'low' | 'good' | 'nearly_full' | 'overcommitted'
  status_message: string
}

/** Offer Accepted celebration card data */
export interface OfferAcceptedMoment {
  offer_total: number
  contact_name: string
  pipeline_this_month: number
  is_best_month: boolean
  best_month_label?: string
  best_month_value?: number
}

/** First Offer Sent milestone status */
export interface FirstOfferSentStatus {
  should_show: boolean
}

/** Annual Business Wrapped summary data */
export interface AnnualWrappedData {
  should_show: boolean
  year: number
  offers_sent: number
  offers_won: number
  win_rate: number
  pipeline_value: number
  new_clients: number
  best_month: string
  best_month_value: number
  top_client_name: string
  top_client_value: number
  yoy_growth_pct: number | null
  projects_delivered: number | null
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
  monthly_capacity_hours: number
  draft_watermark_text: string
  draft_disclaimer?: string
  tax_advisor_name?: string
  tax_advisor_email?: string
  enable_orga_integration: boolean
}
