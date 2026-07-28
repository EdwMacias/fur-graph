<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Title,
  Decimation,
} from 'chart.js'

ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  Title,
  Decimation,
)

const props = defineProps({
  panel: { type: Object, required: true },
})

// Paleta por tipo de serie y por estilo de línea/marcador.
const coloresSerie = ['#38bdf8', '#f59e0b', '#a78bfa', '#34d399']
const coloresEstilo = {
  promedio: '#f87171', // rojo (peso estático promedio)
  maximo: '#34d399',   // verde (fuerza máxima)
  minimo: '#34d399',   // verde (peso dinámico mínimo)
  auxiliar: '#fb923c', // naranja (máx auxiliar)
}

const rangoX = computed(() => {
  let min = Infinity
  let max = -Infinity
  for (const s of props.panel.series) {
    if (s.muestras.length) {
      min = Math.min(min, s.muestras[0])
      max = Math.max(max, s.muestras[s.muestras.length - 1])
    }
  }
  if (!isFinite(min)) { min = 0; max = 1 }
  return { min, max }
})

const chartData = computed(() => {
  const datasets = []

  // Series principales (líneas de datos)
  props.panel.series.forEach((s, i) => {
    const color = coloresSerie[i % coloresSerie.length]
    const densa = s.valores.length > 400
    datasets.push({
      label: s.nombre,
      data: s.muestras.map((x, k) => ({ x, y: s.valores[k] })),
      borderColor: color,
      backgroundColor: color,
      borderWidth: 1.2,
      pointRadius: densa ? 0 : 2,
      tension: 0,
    })
  })

  // Líneas horizontales (promedio / máximo / mínimo / auxiliar)
  for (const l of props.panel.lineas) {
    const color = coloresEstilo[l.estilo] || '#94a3b8'
    datasets.push({
      label: l.etiqueta,
      data: [
        { x: rangoX.value.min, y: l.valor },
        { x: rangoX.value.max, y: l.valor },
      ],
      borderColor: color,
      backgroundColor: color,
      borderWidth: 1.4,
      borderDash: l.estilo === 'promedio' ? [6, 4] : [3, 3],
      pointRadius: 0,
      tension: 0,
    })
  }

  // Marcadores (punto extremo)
  for (const m of props.panel.marcadores) {
    const color = coloresEstilo[m.estilo] || '#e2e8f0'
    datasets.push({
      label: '',
      data: [{ x: m.muestra, y: m.valor }],
      borderColor: color,
      backgroundColor: color,
      pointRadius: 5,
      pointHoverRadius: 6,
      showLine: false,
    })
  }

  return { datasets }
})

const options = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  parsing: false,
  normalized: true,
  interaction: { mode: 'nearest', intersect: false },
  plugins: {
    title: { display: true, text: props.panel.titulo, color: '#e2e8f0', font: { size: 14 } },
    legend: {
      labels: {
        color: '#cbd5e1',
        boxWidth: 12,
        filter: (item) => item.text !== '',
      },
    },
    decimation: { enabled: true, algorithm: 'lttb', samples: 800 },
    tooltip: { enabled: true },
  },
  scales: {
    x: {
      type: 'linear',
      title: { display: true, text: 'Número de muestra', color: '#94a3b8' },
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(148,163,184,0.12)' },
    },
    y: {
      title: { display: true, text: props.panel.y_label, color: '#94a3b8' },
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(148,163,184,0.12)' },
    },
  },
}))
</script>

<template>
  <div class="grafico-wrap">
    <Line :data="chartData" :options="options" />
  </div>
</template>
