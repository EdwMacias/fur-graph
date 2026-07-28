<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { listarPruebas } from '../api'
import SubirFur from '../components/SubirFur.vue'

const router = useRouter()
const pruebas = ref([])
const error = ref('')
let timer = null

async function cargar() {
  try {
    pruebas.value = await listarPruebas()
    error.value = ''
  } catch (e) {
    error.value = 'No se pudo conectar con la API'
  }
}

function abrir(p) {
  router.push({ name: 'detalle', params: { id: p.id } })
}

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

onMounted(() => {
  cargar()
  timer = setInterval(cargar, 5000) // polling: ver pruebas conforme llegan
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <SubirFur @subido="cargar" />

  <div class="tarjeta">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <strong>Pruebas recibidas</strong>
      <span class="muted">Actualiza cada 5 s</span>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!pruebas.length" class="muted">Aún no hay pruebas. Sube un FUR o espera a que lleguen.</p>
    <table v-else>
      <thead>
        <tr>
          <th>IdPrueba</th><th>Tipo</th><th>Esquema</th>
          <th>Fecha prueba</th><th>Recibido</th><th>Tamaño</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in pruebas" :key="p.id" @click="abrir(p)">
          <td>{{ p.id_prueba ?? '—' }}</td>
          <td><span class="chip" :class="p.tipo.toLowerCase()">{{ p.tipo }}</span></td>
          <td>{{ p.esquema }}</td>
          <td>{{ fmt(p.fecha_prueba) }}</td>
          <td>{{ fmt(p.recibido_en) }}</td>
          <td>{{ (p.bytes / 1024).toFixed(1) }} KB</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
