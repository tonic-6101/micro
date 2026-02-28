// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

/**
 * Translation wrapper for i18n support.
 * Uses Frappe's built-in translation system when available,
 * falls back to passthrough when not loaded.
 */
export function __(msg: string, replace?: Record<string, string>): string {
  // Use Frappe's global translation function if available
  const win = window as Record<string, unknown>
  if (typeof win.__ === 'function') {
    return (win.__ as (msg: string, replace?: Record<string, string>) => string)(
      msg,
      replace
    )
  }
  // Fallback: simple placeholder replacement
  if (replace) {
    let result = msg
    for (const [key, value] of Object.entries(replace)) {
      result = result.replace(`{${key}}`, value)
    }
    return result
  }
  return msg
}
