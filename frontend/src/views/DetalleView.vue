<script setup>
import { ref, onMounted } from 'vue'
import { obtenerDatos } from '../api'
import GraficoLinea from '../components/GraficoLinea.vue'
import PanelMetricas from '../components/PanelMetricas.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })

const datos = ref(null)
const error = ref('')
const cargando = ref(true)

onMounted(async () => {
  try {
    datos.value = await obtenerDatos(props.id)
  } catch (e) {
    error.value = e.response?.data?.detail || 'No se pudieron cargar los datos'
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <p><router-link to="/">← Volver al listado</router-link></p>

  <p v-if="cargando" class="muted">Cargando…</p>
  <p v-else-if="error" class="error">{{ error }}</p>

  <template v-else-if="datos">
    <div class="tarjeta">
      <h2 style="margin:0 0 4px">
        {{ datos.tipo === 'FRENOS' ? 'Prueba de Frenos' : 'Prueba de Suspensión' }}
        <span class="muted">· IdPrueba {{ datos.id_prueba ?? '—' }} · esquema {{ datos.esquema }}</span>
      </h2>
      <PanelMetricas :metricas="datos.metricas" />
    </div>

    <div class="grid-2">
      <div v-for="(panel, i) in datos.paneles" :key="i" class="tarjeta">
        <GraficoLinea :panel="panel" />
      </div>
    </div>
  </template>
</template>
