// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

/**
 * The bounds a form has to obey, as the server stated them.
 *
 * `micro.html` writes each boot key onto `window`, so the values are there
 * before the first render — no screen waits on a request to learn what it may
 * accept. The dev server serves no boot data, hence the fallbacks, which match
 * the defaults in `micro/limits.py`.
 */

/** Mirrors DEFAULT_MAX_EXPECTED_VALUE in micro/limits.py. */
const FALLBACK_MAX_EXPECTED_VALUE = 1_000_000

interface MicroLimits {
  max_expected_value?: number
}

function boot(): MicroLimits {
  return ((window as unknown as Record<string, unknown>).micro_limits as MicroLimits) || {}
}

/** Largest expected value a lead may carry. 0 means the ceiling is switched off. */
export function maxExpectedValue(): number {
  const value = boot().max_expected_value
  return value === undefined || value === null ? FALLBACK_MAX_EXPECTED_VALUE : Number(value)
}

/** The range as a person reads it — '0 – 1.000.000 €', or '' when uncapped. */
export function expectedValueRange(): string {
  const max = maxExpectedValue()
  if (!max) return ''

  const money = (value: number) =>
    value.toLocaleString('de-DE', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    })

  return `${money(0)} – ${money(max)}`
}
