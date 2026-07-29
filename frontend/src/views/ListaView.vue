<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { listarPruebas } from '../api'
import SubirFur from '../components/SubirFur.vue'

const router = useRouter()
const pruebas = ref([])
const error = ref('')
const cargandoMas = ref(false)
const hayMas = ref(false)
let timer = null

const LIMITE = 100
const filtroTipo = ref('')
const filtroId = ref('')

function filtros(extra) {
  const f = {}
  if (filtroTipo.value) f.tipo = filtroTipo.value
  if (filtroId.value) f.id_prueba = filtroId.value
  return { ...f, ...extra }
}

// Refresca la ventana ya cargada (al menos LIMITE) desde el principio, sin
// perder las páginas que el usuario ya trajo con "Cargar más".
async function refrescar() {
  try {
    const cantidad = Math.max(pruebas.value.length, LIMITE)
    const r = await listarPruebas(filtros({ limit: cantidad, offset: 0 }))
    pruebas.value = r
    hayMas.value = r.length === cantidad
    error.value = ''
  } catch (e) {
    error.value = 'No se pudo conectar con la API'
  }
}

async function cargarMas() {
  cargandoMas.value = true
  try {
    const r = await listarPruebas(filtros({ limit: LIMITE, offset: pruebas.value.length }))
    pruebas.value = pruebas.value.concat(r)
    hayMas.value = r.length === LIMITE
  } catch (e) {
    error.value = 'No se pudo conectar con la API'
  } finally {
    cargandoMas.value = false
  }
}

function aplicarFiltros() {
  pruebas.value = []
  refrescar()
}

function abrir(p) {
  router.push({ name: 'detalle', params: { id: p.id } })
}

function fmt(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

onMounted(() => {
  refrescar()
  timer = setInterval(refrescar, 5000) // polling: ver pruebas conforme llegan
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <SubirFur @subido="aplicarFiltros" />

  <div class="tarjeta">
    <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center; margin-bottom:12px;">
      <select v-model="filtroTipo" @change="aplicarFiltros">
        <option value="">Todos los tipos</option>
        <option value="FRENOS">Frenos</option>
        <option value="SUSPENSION">Suspensión</option>
        <option value="ALINEACION">Alineación</option>
        <option value="RUIDOS">Ruidos</option>
      </select>
      <input
        type="number"
        v-model="filtroId"
        placeholder="Buscar por IdPrueba"
        style="width:180px"
        @keyup.enter="aplicarFiltros"
      />
      <button class="secundario" @click="aplicarFiltros">Buscar</button>
    </div>

    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <strong>Pruebas recibidas ({{ pruebas.length }})</strong>
      <span class="muted">Actualiza cada 5 s</span>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!pruebas.length" class="muted">No hay pruebas con esos filtros.</p>
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
    <div v-if="hayMas" style="text-align:center; margin-top:12px">
      <button class="secundario" :disabled="cargandoMas" @click="cargarMas">
        {{ cargandoMas ? 'Cargando…' : 'Cargar más' }}
      </button>
    </div>
  </div>
</template>
