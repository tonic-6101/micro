// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Tonic

// ESM entry point for Micro's settings component.
// Dock's DockSettingsAppHost lazy-loads this bundle and renders MicroSettings
// inside the Dock SPA at /dock/settings/app/micro.
//
// This file is built as a separate Vite library entry: micro-settings.esm.js

export { default as MicroSettings } from './pages/Settings.vue'
