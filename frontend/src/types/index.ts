// =============================================================================
// types/index.ts — Domain type definitions for Pila Studio Management
// Every type mirrors the backend Pydantic schema exactly so TypeScript can
// catch mismatches at compile time rather than at runtime in production.
// All IDs are string (UUID v4), all timestamps are ISO 8601 strings.
// =============================================================================

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

// User roles — ordered from highest to lowest privilege
export type Role =
  | 'developer'     // full access, can manage any branch
  | 'owner'         // full access within their partner (multi-branch)
  | 'branch_master' // manages a single branch
  | 'admin'         // day-to-day operations in a branch
  | 'trainer'       // limited: deduct sessions, view own bookings

// Order lifecycle — mirrors payment completion state
export type OrderStatus = 'pending' | 'paid' | 'partial' | 'cancelled'

// Booking lifecycle
export type BookingStatus = 'pending' | 'confirmed' | 'cancelled'

// Session hour transaction direction
export type TransactionType =
  | 'DEDUCT'  // subtract hours (session used)
  | 'ADJUST'  // manual correction (positive or negative)
  | 'ADD'     // hours added (new order)

// Payment instrument options
export type PaymentMethod = 'credit' | 'bank_transfer' | 'cash'

// Package billing model
export type PackageType =
  | 'sale'      // standard: pay to buy hours
  | 'pre_sale'  // pre-sale promo, may have different pricing rules

// ---------------------------------------------------------------------------
// Auth / User
// ---------------------------------------------------------------------------

// Returned by GET /auth/me — the logged-in user's profile
export interface CurrentUser {
  readonly id: string
  display_name: string
  email: string
  role: Role
  // null for developer/owner (not locked to a single branch)
  branch_id: string | null
  // partner groups branches together under an owner
  partner_id: string | null
}

// Returned by GET /users — user management list entries
export interface User {
  readonly id: string
  username: string
  display_name: string
  email: string
  role: Role
  branch_id: string | null
  status: 'active' | 'inactive'
}

// ---------------------------------------------------------------------------
// Branch & Source Types
// ---------------------------------------------------------------------------

// A studio location — customers and staff belong to a branch
export interface Branch {
  readonly id: string
  name: string
  prefix: string        // short code used in customer code generation (e.g. "BKK")
  partner_id: string
}

// How a customer heard about / enrolled at the branch (e.g. "Walk-in", "Facebook")
export interface SourceType {
  readonly id: string
  label: string         // human-readable display name
  code: string          // short code stored on customer record
  branch_id: string
}

// Full branch detail including configuration — returned by GET /branches/:id
export interface BranchDetail extends Branch {
  source_types: SourceType[]
  opening_hour: string | null   // "HH:MM" format
  closing_hour: string | null   // "HH:MM" format
}

// ---------------------------------------------------------------------------
// Trainer
// ---------------------------------------------------------------------------

export interface Trainer {
  readonly id: string
  name: string
  display_name: string  // shown in dropdowns (often "ชื่อเล่น")
  email: string | null
  branch_id: string
  status: 'active' | 'inactive'
  profile_photo_url: string | null
}

// ---------------------------------------------------------------------------
// Caretaker (ผู้ดูแลเด็ก)
// ---------------------------------------------------------------------------

export interface Caretaker {
  readonly id: string
  name: string
  email: string | null
  branch_id: string
  status: 'active' | 'inactive'
}

// ---------------------------------------------------------------------------
// Package
// ---------------------------------------------------------------------------

export interface Package {
  readonly id: string
  name: string
  hours: number               // total training hours included
  type: PackageType
  price: number               // THB
  branch_id: string | null    // null = available across all branches
  status: 'active' | 'inactive' | 'expired'
  active_from: string | null  // ISO date, null = always active
  active_until: string | null // ISO date, null = never expires
}

// ---------------------------------------------------------------------------
// Customer
// ---------------------------------------------------------------------------

export interface Customer {
  readonly id: string
  code: string              // auto-generated (e.g. "BKK-00123")
  first_name: string
  last_name: string
  nickname: string | null
  display_name: string      // computed from nickname or first_name
  phone: string | null
  line_id: string | null
  email: string | null
  branch_id: string
  trainer_id: string | null    // primary assigned trainer
  caretaker_id: string | null  // assigned caretaker (for children)
  status: 'active' | 'inactive'
  notes: string | null
  profile_photo_url: string | null
  birthday: string | null      // ISO date "YYYY-MM-DD"
  is_duplicate: boolean        // flag for admin review when name collision detected
  remaining_hours: number      // cached from customer_hours table
}

// ---------------------------------------------------------------------------
// Order & Payments
// ---------------------------------------------------------------------------

// A single installment payment recorded against an order
export interface OrderPayment {
  readonly id: string
  method: PaymentMethod
  amount: number   // THB
  paid_at: string  // ISO 8601 datetime
}

// A training package purchase — ties a customer to hours
export interface Order {
  readonly id: string
  order_date: string          // ISO date "YYYY-MM-DD"
  customer_id: string
  customer_code: string       // denormalized for display (CR-01: show code, not UUID)
  customer_name: string
  package_id: string
  package_name: string
  hours: number               // base hours from package
  bonus_hours: number         // promotional extra hours
  price: number               // agreed total price (may differ from package.price)
  price_per_session: number   // derived: price / (hours + bonus_hours)
  outstanding_balance: number // price - sum(payments.amount)
  branch_id: string
  trainer_id: string | null
  caretaker_id: string | null
  is_renewal: boolean         // true when customer buys another package
  notes: string | null
  status: OrderStatus
  payments: OrderPayment[]
}

// ---------------------------------------------------------------------------
// Session / Customer Hours
// ---------------------------------------------------------------------------

// One row in the hours transaction ledger
export interface SessionLogEntry {
  readonly id: string
  customer_id: string
  customer_code: string   // shown in table (CR-01)
  customer_name: string
  transaction_type: TransactionType
  before: number          // balance before this transaction
  amount: number          // hours changed (positive = add, negative = subtract)
  after: number           // balance after this transaction
  actor_id: string
  actor_name: string      // who performed the deduction/adjustment
  trainer_id: string | null
  trainer_name: string | null
  created_at: string      // ISO 8601 datetime
}

// Request body for POST /customer-hours/deduct
export interface DeductSessionPayload {
  customer_id: string
  branch_id: string
}

// Request body for PUT /customer-hours/adjust
export interface AdjustHoursPayload {
  customer_id: string
  amount: number    // positive = add hours, negative = subtract hours
  reason: string
}

// ---------------------------------------------------------------------------
// Booking
// ---------------------------------------------------------------------------

export interface Booking {
  readonly id: string
  customer_id: string
  customer_name: string
  trainer_id: string
  trainer_name: string
  start_at: string    // ISO 8601 datetime
  end_at: string      // ISO 8601 datetime
  status: BookingStatus
  branch_id: string
  notes: string | null
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

// One KPI card shown on the dashboard
export interface DashboardMetric {
  label: string
  value: number
  // percentage change vs previous period — null when comparison is not available
  trend: number | null
  unit: string | null   // e.g. "ชั่วโมง", "บาท", null for counts
}

export interface DashboardData {
  metrics: DashboardMetric[]
  period: 'today' | 'week' | 'month' | 'custom'
}

// ---------------------------------------------------------------------------
// Permissions & Feature Toggles
// ---------------------------------------------------------------------------

// One cell in the permission matrix (role × module × action)
export interface PermissionCell {
  role: Role
  module: string
  action: 'view' | 'create' | 'edit' | 'delete'
  allowed: boolean
}

// Module-level on/off switch — controlled by owner/developer
export interface FeatureToggle {
  module: string   // unique key, e.g. "bookings", "signature_print"
  label: string    // Thai display name shown in settings
  enabled: boolean
}

// ---------------------------------------------------------------------------
// Activity Log
// ---------------------------------------------------------------------------

export interface ActivityLogEntry {
  readonly id: string
  actor_id: string
  actor_name: string
  action: string                  // e.g. "CREATE_ORDER", "DEDUCT_SESSION"
  target_type: string             // e.g. "Customer", "Order"
  target_id: string
  // before/after diff — null when the action has no state change (e.g. login)
  changes: Record<string, { before: unknown; after: unknown }> | null
  created_at: string              // ISO 8601 datetime
  branch_id: string | null
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export interface Settings {
  language: 'th' | 'en'
  dark_mode: boolean
  google_connected: boolean
  google_drive_used_bytes: number | null
  google_drive_total_bytes: number | null
}

// ---------------------------------------------------------------------------
// Shared / Utility
// ---------------------------------------------------------------------------

// Standard paginated list response — all list endpoints return this shape
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// Query parameters accepted by all list endpoints
export interface ListParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  branch_id?: string
  status?: string
  // date range filters (ISO date strings "YYYY-MM-DD")
  start_date?: string
  end_date?: string
  // entity-specific filters passed through the same interface
  trainer_id?: string
  customer_id?: string
  role?: Role
}
