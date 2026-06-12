/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Inter', 'ui-sans-serif', 'system-ui', '-apple-system',
          'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif',
        ],
      },
      colors: {
        // Bound to CSS custom properties so the whole identity can be
        // re-skinned at runtime from BrandingConfig (white-label core).
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        surface: {
          DEFAULT: 'rgb(var(--color-surface) / <alpha-value>)',
          raised: 'rgb(var(--color-surface-raised) / <alpha-value>)',
          overlay: 'rgb(var(--color-surface-overlay) / <alpha-value>)',
        },
        edge: 'rgb(var(--color-edge) / <alpha-value>)',
      },
      boxShadow: {
        glow: '0 0 24px rgb(var(--color-primary) / 0.35)',
        'glow-sm': '0 0 12px rgb(var(--color-primary) / 0.25)',
      },
    },
  },
  plugins: [],
}
