<script setup>
import { computed } from 'vue'

const props = defineProps({
  metricas: { type: Object, required: true },
})

// Etiquetas legibles y orden preferente. Las claves no listadas se muestran
// con un formateo genérico del nombre.
const etiquetas = {
  eficacia_total: 'Eficacia total',
  eficacia_auxiliar: 'Eficacia auxiliar',
  peso_total: 'Peso total',
  peso_e1_izq: 'Peso Eje 1 Izq (prom.)',
  peso_e1_der: 'Peso Eje 1 Der (prom.)',
  peso_e2_izq: 'Peso Eje 2 Izq (prom.)',
  peso_e2_der: 'Peso Eje 2 Der (prom.)',
  fmax_e1_izq: 'Fuerza máx Eje 1 Izq',
  fmax_e1_der: 'Fuerza máx Eje 1 Der',
  fmax_e2_izq: 'Fuerza máx Eje 2 Izq',
  fmax_e2_der: 'Fuerza máx Eje 2 Der',
  fmax_aux_izq: 'Fuerza máx Aux Izq',
  fmax_aux_der: 'Fuerza máx Aux Der',
  peso_e1_promedio: 'Peso Eje 1 (prom.)',
  peso_e1_desviacion: 'Peso Eje 1 (desv.)',
  peso_e2_promedio: 'Peso Eje 2 (prom.)',
  peso_e2_desviacion: 'Peso Eje 2 (desv.)',
  fuerza_e1_maximo: 'Fuerza Eje 1 (máx)',
  fuerza_e2_maximo: 'Fuerza Eje 2 (máx)',
  bufferalineacioneje1_promedio: 'Alineación Eje 1 (prom.)',
  bufferalineacioneje2_promedio: 'Alineación Eje 2 (prom.)',
  ruido_promedio: 'Ruido promedio',
  ruido_maximo: 'Ruido máximo',
}

const destacadas = new Set(['eficacia_total', 'eficacia_auxiliar'])
const porcentaje = new Set(['eficacia_total', 'eficacia_auxiliar'])

function etiqueta(k) {
  return etiquetas[k] || k.replaceAll('_', ' ')
}

function valor(k, v) {
  if (typeof v === 'number') {
    return porcentaje.has(k) ? `${v.toFixed(2)} %` : v.toFixed(2)
  }
  return v
}

const items = computed(() =>
  Object.entries(props.metricas).map(([k, v]) => ({
    k,
    label: etiqueta(k),
    val: valor(k, v),
    destacada: destacadas.has(k),
  })),
)
</script>

<template>
  <div class="metricas">
    <div v-for="it in items" :key="it.k" class="metrica" :class="{ destacada: it.destacada }">
      <div class="k">{{ it.label }}</div>
      <div class="v">{{ it.val }}</div>
    </div>
  </div>
</template>
