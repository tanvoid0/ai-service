/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d7ff',
          300: '#a4b8ff',
          400: '#667eea',
          500: '#764ba2',
          600: '#5a3d7a',
          700: '#4a2f62',
          800: '#3d2550',
          900: '#332042',
        },
      },
    },
  },
  plugins: [],
}

