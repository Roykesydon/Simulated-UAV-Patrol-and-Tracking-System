/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    themes: {
      dark: {
        colors: {
          primary: '#5582d5',
          // secondary: '#5CBBF6',
          // primary_dark: '#5582d5'
          // primary_dark: '#2f649f'
        },
      },
    },
    defaultTheme: 'dark',
  },
})
