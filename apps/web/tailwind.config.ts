import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Core background & canvas
        canvas: '#090d16',
        background: '#090d16',

        // Surfaces
        surface: '#0e1417',
        'surface-container-lowest': '#080f12',
        'surface-container-low': '#161d1f',
        'surface-container': '#1a2123',
        'surface-container-high': '#242b2e',
        'surface-container-highest': '#2f3639',
        'surface-bright': '#333a3d',
        'surface-variant': '#2f3639',

        // Typography colors
        'on-surface': '#dde3e7',
        'on-surface-variant': '#bbc9cf',
        'on-background': '#dde3e7',

        // Borders & Outlines
        outline: '#859398',
        'outline-variant': '#262626',
        'outline-muted': '#3c494e',

        // Primary Brand (Cyber Blue / Cyan)
        brand: '#00D4FF',
        primary: '#00D4FF',
        'primary-container': '#0cd4ff',
        'on-primary': '#003542',
        'on-primary-container': '#00586b',
        'primary-fixed': '#b4ebff',
        'primary-fixed-dim': '#3ed7ff',

        // Secondary (Muted Cyan / Blue)
        secondary: '#9ccee1',
        'secondary-container': '#154d5d',
        'on-secondary': '#003543',
        'on-secondary-container': '#8abdcf',
        'secondary-fixed': '#b7eafe',
        'secondary-fixed-dim': '#9ccee1',

        // Severities & Statuses (aligned with CSPM & Stitch specifications)
        critical: '#ef4444',
        error: '#ef4444',
        'error-container': '#93000a',
        'on-error': '#ffffff',
        'on-error-container': '#ffdad6',

        high: '#f97316',
        'tertiary-container': '#feb528',
        'on-tertiary-container': '#6c4900',

        medium: '#eab308',
        low: '#3b82f6',

        passed: '#22c55e',
        success: '#22c55e',
      },
      fontFamily: {
        headline: ['"Space Grotesk"', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        label: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
      },
    },
  },
  plugins: [],
} satisfies Config
