import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Chart, registerables } from 'chart.js'

import App from './App.vue'
import router from './router'
import './style.css'

// Регистрируем все Chart.js компоненты глобально
Chart.register(...registerables)

const app = createApp(App)

app.directive('click-outside', {
  mounted(el, binding) {
    el.clickOutsideEvent = function(event) {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value(event);
      }
    };
    document.body.addEventListener('click', el.clickOutsideEvent);
  },
  unmounted(el) {
    document.body.removeEventListener('click', el.clickOutsideEvent);
  }
});

app.use(createPinia())
app.use(router)
app.mount('#app')
