// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

/** A parsed import file: uniform rows of string-keyed values. */
export interface ParsedTable {
  columns: string[]
  rows: Record<string, unknown>[]
  format: 'csv' | 'jsonl' | 'json'
  /** Lines that could not be parsed — reported, never silently dropped. */
  badLines: number[]
}

/** Split a CSV line-set per RFC 4180: quoted fields, "" escapes, embedded newlines. */
function parseCsv(text: string, delimiter: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let quoted = false
  let i = 0

  const endField = () => {
    row.push(field)
    field = ''
  }
  const endRow = () => {
    endField()
    rows.push(row)
    row = []
  }

  while (i < text.length) {
    const char = text[i]

    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i += 2
          continue
        }
        quoted = false
        i += 1
        continue
      }
      field += char
      i += 1
      continue
    }

    if (char === '"' && field === '') {
      quoted = true
      i += 1
    } else if (char === delimiter) {
      endField()
      i += 1
    } else if (char === '\r' && text[i + 1] === '\n') {
      endRow()
      i += 2
    } else if (char === '\n' || char === '\r') {
      endRow()
      i += 1
    } else {
      field += char
      i += 1
    }
  }

  if (field !== '' || row.length) endRow()

  return rows.filter((r) => r.some((cell) => cell !== ''))
}

/** German exports commonly use semicolons — pick whichever wins on the header. */
function detectDelimiter(text: string): string {
  const header = text.slice(0, text.indexOf('\n') === -1 ? text.length : text.indexOf('\n'))
  const counts = [',', ';', '\t'].map((d) => ({ d, n: header.split(d).length - 1 }))
  counts.sort((a, b) => b.n - a.n)
  return counts[0].n > 0 ? counts[0].d : ','
}

/** Nested JSON values are flattened to text so every column stays displayable. */
function flatten(value: unknown): unknown {
  if (value === null || value === undefined) return ''
  if (typeof value === 'object') return JSON.stringify(value)
  return value
}

function fromRecords(records: Record<string, unknown>[], format: ParsedTable['format'], badLines: number[]): ParsedTable {
  const columns: string[] = []
  for (const record of records) {
    for (const key of Object.keys(record)) {
      if (!columns.includes(key)) columns.push(key)
    }
  }

  const rows = records.map((record) => {
    const row: Record<string, unknown> = {}
    for (const key of columns) row[key] = flatten(record[key])
    return row
  })

  return { columns, rows, format, badLines }
}

/**
 * Parse an uploaded import file.
 *
 * JSONL is one JSON object per line; a bad line is recorded and skipped rather
 * than aborting a 3,000-line file over one malformed row.
 */
export function parseTable(text: string, filename: string): ParsedTable {
  const name = filename.toLowerCase()
  const trimmed = text.trim()

  if (name.endsWith('.jsonl') || name.endsWith('.ndjson')) {
    const records: Record<string, unknown>[] = []
    const badLines: number[] = []
    text.split(/\r?\n/).forEach((line, index) => {
      if (!line.trim()) return
      try {
        const parsed = JSON.parse(line)
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) records.push(parsed)
        else badLines.push(index + 1)
      } catch {
        badLines.push(index + 1)
      }
    })
    return fromRecords(records, 'jsonl', badLines)
  }

  if (name.endsWith('.json') || trimmed.startsWith('[')) {
    const parsed = JSON.parse(trimmed)
    const records = (Array.isArray(parsed) ? parsed : [parsed]).filter(
      (r) => r && typeof r === 'object',
    )
    return fromRecords(records, 'json', [])
  }

  const delimiter = detectDelimiter(text)
  const table = parseCsv(text, delimiter)
  if (!table.length) return { columns: [], rows: [], format: 'csv', badLines: [] }

  const columns = table[0].map((c, i) => c.trim() || `column_${i + 1}`)
  const records = table.slice(1).map((cells) => {
    const record: Record<string, unknown> = {}
    columns.forEach((column, i) => {
      record[column] = cells[i] ?? ''
    })
    return record
  })

  return { columns, rows: records, format: 'csv', badLines: [] }
}

/** Guess which source column belongs to a target field, from its hint words. */
export function guessColumn(columns: string[], hints: string[]): string {
  const normalise = (s: string) => s.toLowerCase().replace(/[\s_-]+/g, '')
  const normalised = columns.map((c) => ({ column: c, key: normalise(c) }))

  for (const hint of hints) {
    const exact = normalised.find((c) => c.key === normalise(hint))
    if (exact) return exact.column
  }
  for (const hint of hints) {
    const partial = normalised.find((c) => c.key.includes(normalise(hint)))
    if (partial) return partial.column
  }
  return ''
}
