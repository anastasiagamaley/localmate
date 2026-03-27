/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg:      '#0a0a0f',
        surface: '#111118',
        card:    '#16161f',
        border:  '#22222e',
        accent:  '#7c5cfc',
        accent2: '#00e5a0',
        muted:   '#7a7a9a',
        gold:    '#f5c842',
      },
      fontFamily: {
        sans:    ['Manrope', 'sans-serif'],
        display: ['Unbounded', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
