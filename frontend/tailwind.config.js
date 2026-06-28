/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', '"SF Pro Text"', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        blue: '#2997FF',
        gray: {
          DEFAULT: '#86868b',
          100: '#94928d',
          200: '#afafaf',
          300: '#42424570',
        },
        zinc: '#101010',
      },
      boxShadow: {
        glow: '0 0 40px rgba(41,151,255,0.2)',
      },
    },
  },
  plugins: [],
}
