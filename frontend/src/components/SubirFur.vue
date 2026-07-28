<script setup>
import { ref } from 'vue'
import { subirFur } from '../api'

const emit = defineEmits(['subido'])

// La API key se recuerda en localStorage para el MVP de carga manual.
const apiKey = ref(localStorage.getItem('fur_api_key') || '')
const archivo = ref(null)
const cargando = ref(false)
const mensaje = ref('')
const esError = ref(false)

function onFile(e) {
  archivo.value = e.target.files[0] || null
}

async function subir() {
  if (!archivo.value || !apiKey.value) return
  cargando.value = true
  mensaje.value = ''
  esError.value = false
  localStorage.setItem('fur_api_key', apiKey.value)
  try {
    const r = await subirFur(archivo.value, apiKey.value)
    mensaje.value = `Cargado: ${r.tipo} (${r.esquema}) #${r.id}`
    emit('subido')
  } catch (err) {
    esError.value = true
    mensaje.value = err.response?.data?.detail || 'Error al subir el archivo'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="tarjeta">
    <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
      <input type="password" v-model="apiKey" placeholder="X-API-Key" style="width:200px" />
      <input type="file" accept="application/json,.json" @change="onFile" />
      <button :disabled="cargando || !archivo || !apiKey" @click="subir">
        {{ cargando ? 'Subiendo…' : 'Subir FUR' }}
      </button>
      <span :class="{ error: esError, muted: !esError }">{{ mensaje }}</span>
    </div>
  </div>
</template>
