import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Inject JWT token from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refresh })
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  register:      (data) => api.post('/auth/register', data),
  login:         (data) => api.post('/auth/login', data),
  refresh:       (data) => api.post('/auth/refresh', data),
  deleteAccount: ()     => api.delete('/auth/me'),
}

// ─── Users / Profile ──────────────────────────────────────────────────────────
export const usersApi = {
  getMe:          ()     => api.get('/users/me'),
  updateMe:       (data) => api.patch('/users/me', data),
  getProfile:     (id)   => api.get(`/users/${id}`),
  getXp:          (id)   => api.get(`/users/${id}/xp`),
}

// ─── Search ───────────────────────────────────────────────────────────────────
export const searchApi = {
  search: (data) => api.post('/search/', data),
}

// ─── Tokens ───────────────────────────────────────────────────────────────────
export const tokensApi = {
  getBalance:   ()     => api.get('/tokens/balance'),
  openContact:  (data) => api.post('/tokens/open-contact', data),
  payGig:       (data) => api.post('/tokens/pay-gig', data),
  getHistory:   ()     => api.get('/tokens/history'),
}

// ─── Gigs ─────────────────────────────────────────────────────────────────────
export const gigsApi = {
  priceCheck:  (data)    => api.post('/gigs/price-check', data),
  create:      (data)    => api.post('/gigs/', data),
  myGigs:      (status)  => api.get('/gigs/my', { params: status ? { status } : {} }),
  getGig:      (id)      => api.get(`/gigs/${id}`),
  accept:      (id)      => api.post(`/gigs/${id}/accept`),
  complete:    (id)      => api.post(`/gigs/${id}/complete`),
  cancel:      (id, reason) => api.post(`/gigs/${id}/cancel`, { reason }),
}
export default api
