import axios from 'axios'

// En dev el proxy de Vite reenvía /api al backend; en prod se puede fijar
// VITE_API_BASE al dominio de la API. Por defecto usa la misma raíz.
const baseURL = import.meta.env.VITE_API_BASE || ''

export const api = axios.create({ baseURL })

export function listarPruebas(tipo) {
  const params = tipo ? { tipo } : {}
  return api.get('/api/pruebas', { params }).then((r) => r.data)
}

export function obtenerDatos(id) {
  return api.get(`/api/pruebas/${id}/datos`).then((r) => r.data)
}

export function subirFur(file, apiKey) {
  const form = new FormData()
  form.append('file', file)
  return api
    .post('/api/pruebas', form, { headers: { 'X-API-Key': apiKey } })
    .then((r) => r.data)
}
