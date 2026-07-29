<script setup>
import { ref } from 'vue'
import { iniciarSesion } from '../api'

const emit = defineEmits(['autenticado'])

const apiKey = ref('')
const cargando = ref(false)
const error = ref('')

async function entrar() {
  if (!apiKey.value) return
  cargando.value = true
  error.value = ''
  try {
    await iniciarSesion(apiKey.value)
    apiKey.value = ''
    emit('autenticado')
  } catch (e) {
    error.value = e.response?.data?.detail || 'API key inválida'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="login-gate">
    <div class="tarjeta login-caja">
      <h2 style="margin-top:0">Visor FUR</h2>
      <p class="muted">Ingresa la API key para ver las pruebas.</p>
      <form @submit.prevent="entrar" style="display:flex; flex-direction:column; gap:10px">
        <input type="password" v-model="apiKey" placeholder="X-API-Key" autofocus />
        <button type="submit" :disabled="cargando || !apiKey">
          {{ cargando ? 'Verificando…' : 'Entrar' }}
        </button>
        <span v-if="error" class="error">{{ error }}</span>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-gate {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-caja {
  width: 100%;
  max-width: 340px;
}
</style>
