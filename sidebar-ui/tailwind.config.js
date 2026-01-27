/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        neon: {
          blue: '#00d4ff',
          purple: '#7c3aed',
          glow: 'rgba(0, 212, 255, 0.5)',
        },
        dark: {
          900: '#0a0a0f',
          800: '#12121a',
          700: '#1a1a24',
          600: '#24242e',
        }
      },
      boxShadow: {
        'neon': '0 0 20px rgba(0, 212, 255, 0.3), 0 0 40px rgba(0, 212, 255, 0.1)',
        'neon-strong': '0 0 30px rgba(0, 212, 255, 0.5), 0 0 60px rgba(0, 212, 255, 0.2)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { 
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)',
            filter: 'brightness(1)'
          },
          '50%': { 
            boxShadow: '0 0 40px rgba(0, 212, 255, 0.5)',
            filter: 'brightness(1.1)'
          },
        }
      }
    },
  },
  plugins: [],
}
