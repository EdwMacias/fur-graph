<script setup>
import { ref, onMounted } from 'vue'
import { estadoSesion, cerrarSesion } from './api'
import LoginGate from './components/LoginGate.vue'

const autenticado = ref(false)
const verificando = ref(true)

async function verificar() {
  verificando.value = true
  try {
    autenticado.value = await estadoSesion()
  } catch (e) {
    autenticado.value = false
  } finally {
    verificando.value = false
  }
}

async function salir() {
  await cerrarSesion()
  autenticado.value = false
}

onMounted(verificar)
</script>

<template>
  <template v-if="verificando" />
  <LoginGate v-else-if="!autenticado" @autenticado="verificar" />
  <template v-else>
    <div class="barra">
      <h1><router-link to="/">Visor FUR</router-link></h1>
      <span class="muted">Frenos · Suspensión · Alineación · Ruidos</span>
      <button class="secundario" @click="salir">Cerrar sesión</button>
    </div>
    <div class="contenedor">
      <router-view />
    </div>
  </template>
</template>
