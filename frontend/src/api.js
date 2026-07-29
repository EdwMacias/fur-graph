import axios from 'axios'

// En dev el proxy de Vite reenvía /api al backend; en prod se puede fijar
// VITE_API_BASE al dominio de la API. Por defecto usa la misma raíz.
const baseURL = import.meta.env.VITE_API_BASE || ''

// withCredentials: la cookie de sesión (fur_session) viaja en cada request.
export const api = axios.create({ baseURL, withCredentials: true })

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

export function estadoSesion() {
  return api.get('/api/sesion').then((r) => r.data.autenticado)
}

export function iniciarSesion(apiKey) {
  return api.post('/api/sesion', null, { headers: { 'X-API-Key': apiKey } }).then((r) => r.data)
}

export function cerrarSesion() {
  return api.delete('/api/sesion').then((r) => r.data)
}
