import dockPreset from '../../dock/frontend/src/styles/dock-tailwind-preset.js'

/** @type {import('tailwindcss').Config} */
export default {
  presets: [dockPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts}',
    // Dock shared pages loaded at runtime via ESM — scan source so
    // Tailwind generates the utility classes they use (calendar, people, etc.)
    '../../dock/frontend/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
}
