/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './visa_main/templates/**/*.html',
    './pump_site/templates/**/*.html',
    './hart_site/templates/**/*.html',
    './templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#021D38',
          800: '#042C53',
          700: '#0B3D6B',
          600: '#185FA5',
          500: '#378ADD',
          100: '#E6F1FB',
        },
        brand: '#185FA5',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-up':    'fadeUp 0.6s ease forwards',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%':   { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
