import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import ListaView from './views/ListaView.vue'
import DetalleView from './views/DetalleView.vue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'lista', component: ListaView },
    { path: '/prueba/:id', name: 'detalle', component: DetalleView, props: true },
  ],
})

createApp(App).use(router).mount('#app')
