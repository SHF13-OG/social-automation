import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: '#1e2a3a',
        charcoal: '#2d3748',
        'navy-charcoal': '#252f3f',
        'accent-beige': '#E8D5B7',
        'accent-gold': '#C9A962',
        cream: '#f5f0e8',
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
      },
    },
  },
  plugins: [],
}

export default config
