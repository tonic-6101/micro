// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

/** Acquisition channel — keep in sync with MICRO_SOURCE_OPTIONS in micro/constants.py */
export type MicroSource =
  | 'Manual'
  | 'Classifieds'
  | 'Google Ads'
  | 'Facebook'
  | 'Instagram'
  | 'LinkedIn'
  | 'Email Campaign'
  | 'Cold Call'
  | 'Web Form'
  | 'Organic Search'
  | 'Referral'
  | 'Partner'
  | 'Event'
  | 'Import'
  | 'Other'

export const MICRO_SOURCES: MicroSource[] = [
  'Manual',
  'Classifieds',
  'Google Ads',
  'Facebook',
  'Instagram',
  'LinkedIn',
  'Email Campaign',
  'Cold Call',
  'Web Form',
  'Organic Search',
  'Referral',
  'Partner',
  'Event',
  'Import',
  'Other',
]

/** Frappe Contact with Micro CRM custom fields */
export interface MicroCustomer {
  name: string
  first_name: string
  last_name?: string
  full_name: string
  micro_contact_type: 'Person' | 'Organization'
  /** The organization Contact this person belongs to. Empty for an organization. */
  micro_organization?: string
  micro_status: 'Potential' | 'Active' | 'Inactive'
  company_name?: string
  email_id?: string
  phone?: string
  mobile_no?: string
  micro_website?: string
  micro_source?: MicroSource
  micro_segment?: string
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
  /** Frappe's tag column: ",Altbau,Messe 2026". Written via the tag API. */
  _user_tags?: string
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

/** Micro Segment DocType — durable target group of a contact */
export interface MicroSegment {
  name: string
  segment_name: string
  color?: MicroColor
  sort_order?: number
}

/** Shared colour palette of stages, segments and pipelines */
export type MicroColor = 'Gray' | 'Blue' | 'Green' | 'Yellow' | 'Orange' | 'Red' | 'Purple' | 'Pink'

/** Micro Pipeline DocType — one repeatable sales process */
export interface MicroPipeline {
  name: string
  pipeline_name: string
  segment?: string
  is_default?: boolean
  sort_order?: number
  description?: string
  open_leads?: number
}

/** Micro Pipeline Stage DocType */
export interface MicroPipelineStage {
  name: string
  stage_name: string
  pipeline?: string
  sort_order: number
  color?: MicroColor
  is_closed: boolean
  is_win_stage?: boolean
  is_loss_stage?: boolean
}

/** Contact details denormalised onto a lead card */
export interface LeadContactDetails {
  name: string
  first_name?: string
  last_name?: string
  /** Only set by the single-lead endpoints — the board cards do without it. */
  full_name?: string
  company_name?: string
  email_id?: string
  phone?: string
  mobile_no?: string
  micro_segment?: string
  /** Comma-joined tags, as Frappe stores them for display. */
  _user_tags?: string
  micro_communication_style?: string
  micro_client_loves?: string
  image?: string
  micro_postal_code?: string
  /**
   * Straight-line kilometres from the company postal code in Micro Settings.
   * Worked out server-side; null when either end has no usable postal code.
   */
  distance_km?: number | null
}

/** Micro Lead DocType — one deal in one pipeline */
export interface MicroLead {
  name: string
  lead_name: string
  contact?: string
  status: 'Open' | 'Won' | 'Lost' | 'Archived'
  pipeline?: string
  stage?: string
  stage_name?: string
  priority?: 'Low' | 'Medium' | 'High'
  expected_value?: number
  source?: string
  next_follow_up?: string
  lost_reason?: string
  notes?: string
  contact_details?: LeadContactDetails | null
  last_note?: { subject?: string; date?: string } | null
  is_overdue?: boolean
}

/** Pipeline column: a stage with its leads */
export interface PipelineColumn {
  stage: MicroPipelineStage
  leads: MicroLead[]
  /** Leads in the whole column — may exceed the page that was sent. */
  count: number
  /** How many of them this response actually carries. */
  loaded: number
  value: number
}

/** API response: pipeline Kanban data */
export interface PipelineResponse {
  pipeline: string | null
  stages: PipelineColumn[]
  unassigned: MicroLead[]
  totals: { count: number; value: number }
}

/** API response: pipelines list for the board switcher */
export interface PipelinesListResponse {
  pipelines: MicroPipeline[]
  default: string | null
}

/** What a stage means for the deal — one value instead of two conflicting flags */
export type StageOutcome = 'open' | 'win' | 'loss'

/** A stage as shown in the pipeline management dialog */
export interface PipelineSetupStage {
  name: string
  stage_name: string
  sort_order: number
  color?: MicroColor
  is_closed?: boolean
  outcome: StageOutcome
  lead_count: number
}

/** API response: everything the pipeline management dialog needs */
export interface PipelineSetupResponse {
  pipeline: {
    name: string
    pipeline_name: string
    segment?: string | null
    description?: string | null
    sort_order?: number
    is_default?: boolean
    is_active?: boolean
  }
  stages: PipelineSetupStage[]
  lead_count: number
}

/** The chip for contacts nobody has filed yet — mirrors NO_SEGMENT in customers.py */
export const NO_SEGMENT = '__none__'

/** API response: what categories exist and how many contacts each holds */
export interface CustomerFacets {
  total: number
  segments: (MicroSegment & { count: number })[]
  unsegmented: number
  tags: { tag: string; count: number }[]
}

/** API response: segments list */
export interface SegmentsListResponse {
  segments: MicroSegment[]
}

/** API response: call list / work queue */
export interface CallListResponse {
  leads: MicroLead[]
  total: number
}

/** API response: a single lead, plus whether this user may destroy it */
export interface LeadDetailResponse {
  lead: MicroLead
  can_delete: boolean
}

/** How a logged call went — keep in sync with CALL_OUTCOMES in micro/constants.py */
export type CallOutcome = 'Reached' | 'No Answer' | 'Voicemail' | 'Busy' | 'Wrong Number'

export const CALL_OUTCOMES: CallOutcome[] = ['Reached', 'No Answer', 'Voicemail', 'Busy', 'Wrong Number']

/** One attempt to reach a contact by phone */
export interface CallAttempt {
  name: string
  attempted_at: string
  outcome: CallOutcome
  lead?: string | null
  notes?: string | null
}

/** API response: recent call attempts for a contact */
export interface CallAttemptsResponse {
  attempts: CallAttempt[]
}

/** A day sliced into the spans a caller thinks in — keep in sync with
 * _BUCKET_ORDER in micro/api/call_attempts.py */
export type CallTimeBucket = 'morning' | 'midday' | 'afternoon' | 'evening' | 'other'

/** One (weekday, time-of-day) cell in the call-attempt grid. `weekday` is
 * 0 = Monday .. 6 = Sunday, matching Python's `datetime.weekday()`. */
export interface BestCallTimeCell {
  weekday: number
  bucket: CallTimeBucket
  attempts: number
  reached: number
}

/** API response: when the logged attempts say this contact tends to answer */
export interface BestCallTimeResponse {
  total_attempts: number
  reached_count: number
  best: BestCallTimeCell | null
  grid: BestCallTimeCell[]
}

/** API response: the trash — soft-deleted leads, restorable until purged */
export interface TrashedLeadsResponse {
  leads: MicroLead[]
  total: number
  can_delete: boolean
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

/** What deleting a customer would cost — asked before anything is deleted */
export interface CustomerDeletePreview {
  customer: string
  /** Micro records an erase would take with it, keyed by doctype */
  deletes: Record<string, number>
  /** Documents that must be kept, so an erase is refused */
  retention_blockers: { doctype: string; count: number }[]
  /** Other apps still pointing at this shared Contact */
  foreign_links: { doctype: string; count: number }[]
  can_erase: boolean
}

/** Result of removing or erasing several customers in one request */
export interface BulkDeleteResult {
  mode: 'remove' | 'erase'
  /** Customers the request went through for */
  succeeded: string[]
  /** Customers skipped, with the reason each one was refused */
  failed: { customer: string; error: string }[]
}

/** How much history hangs off a contact, per doctype plus totals */
export interface LinkedDocumentCounts {
  total: number
  /** Documents already sent out — merging repoints these */
  issued: number
  [doctype: string]: number
}

/** One stored duplicate suggestion, with both records attached */
export interface DuplicatePair {
  name: string
  score: number
  band: 'Certain' | 'Likely' | 'Possible'
  signals: string[]
  /** Translated, human-readable version of `signals` */
  reasons: string[]
  contact_a: MicroCustomer
  contact_b: MicroCustomer
  documents_a: LinkedDocumentCounts
  documents_b: LinkedDocumentCounts
}

/** A live match found while a contact is still being typed */
export interface DuplicateMatch {
  contact: MicroCustomer
  score: number
  band: 'Certain' | 'Likely' | 'Possible' | null
  reasons: string[]
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
  /** The contact's tags, already split out of `_user_tags`. */
  tags: string[]
  /** Every lead this contact has ever been in — open ones first. */
  leads: CustomerLead[]
  /** The organization a person belongs to, named rather than a bare docname. */
  organization: OrganizationCard | null
  /** The people who belong to this organization. Empty for a person. */
  members: OrganizationMember[]
}

/** The organization a person belongs to, as the detail page shows it */
export interface OrganizationCard {
  name: string
  full_name?: string
  company_name?: string
  email_id?: string
  phone?: string
  micro_city?: string
}

/** One person at an organization */
export interface OrganizationMember {
  name: string
  first_name?: string
  last_name?: string
  full_name: string
  designation?: string
  email_id?: string
  phone?: string
  mobile_no?: string
  micro_status?: string
  image?: string
}

/** One lead as the customer page shows it: which pipeline, how it ended. */
export interface CustomerLead {
  name: string
  lead_name: string
  status: 'Open' | 'Won' | 'Lost' | 'Archived'
  pipeline?: string
  pipeline_name?: string
  stage?: string
  stage_name?: string
  priority?: 'Low' | 'Medium' | 'High'
  expected_value?: number
  next_follow_up?: string
  lost_reason?: string
  is_open: boolean
  creation?: string
  modified?: string
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

/** One mappable target field of the contact importer */
export interface ImportField {
  field: string
  label: string
  hints: string[]
}

/** How much room is left under the community customer limit */
export interface ImportCapacity {
  limit: number
  used: number
  /** null when the site is unlimited */
  remaining: number | null
  unlimited: boolean
}

/** API response: what the import page needs before a file is chosen */
export interface ImportSetup {
  fields: ImportField[]
  dedupe_keys: string[]
  capacity: ImportCapacity
}

/** API response: the outcome of one imported batch */
export interface ImportResult {
  created: number
  updated: number
  skipped: number
  /** Leads added to the chosen pipeline — new and existing contacts alike. */
  leads_created: number
  failed: number
  failures: { row: number; error: string }[]
  /** Fields left empty because the source value exceeded the column. */
  warned: number
  warnings: { row: number; field: string; reason: string }[]
  limit_reached: boolean
  capacity: ImportCapacity
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
  company_postal_code?: string
  company_city?: string
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
