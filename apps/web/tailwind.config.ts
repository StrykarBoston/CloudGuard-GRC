import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Core background & canvas (Crisp Light Slate / White)
        canvas: '#f8fafc',
        background: '#f8fafc',

        // Surfaces (Crisp White & Layered Slate containers)
        surface: '#ffffff',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f1f5f9',
        'surface-container': '#f8fafc',
        'surface-container-high': '#e2e8f0',
        'surface-container-highest': '#cbd5e1',
        'surface-bright': '#ffffff',
        'surface-variant': '#f1f5f9',

        // Typography colors (High readability slate-900 & slate-600)
        'on-surface': '#0f172a',
        'on-surface-variant': '#475569',
        'on-background': '#0f172a',

        // Borders & Outlines
        outline: '#94a3b8',
        'outline-variant': '#e2e8f0',
        'outline-muted': '#cbd5e1',

        // Primary Brand (Enterprise Vibrant Royal Blue)
        brand: '#2563eb',
        primary: '#2563eb',
        'primary-container': '#1d4ed8',
        'on-primary': '#ffffff',
        'on-primary-container': '#ffffff',
        'primary-fixed': '#dbeafe',
        'primary-fixed-dim': '#bfdbfe',

        // Secondary (Sky / Ice Blue accents)
        secondary: '#0284c7',
        'secondary-container': '#eff6ff',
        'on-secondary': '#ffffff',
        'on-secondary-container': '#1d4ed8',
        'secondary-fixed': '#dbeafe',
        'secondary-fixed-dim': '#93c5fd',

        // Severities & Statuses (Tailored for high contrast on light backgrounds)
        critical: '#dc2626',
        error: '#dc2626',
        'error-container': '#fee2e2',
        'on-error': '#ffffff',
        'on-error-container': '#991b1b',

        high: '#ea580c',
        'tertiary-container': '#ffedd5',
        'on-tertiary-container': '#9a3412',

        medium: '#d97706',
        low: '#2563eb',

        passed: '#16a34a',
        success: '#16a34a',
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
      boxShadow: {
        subtle: '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        card: '0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
        glow: '0 0 15px -3px rgba(37, 99, 235, 0.25)',
      }
    },
  },
  plugins: [],
} satisfies Config
