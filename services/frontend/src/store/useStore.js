import { create } from 'zustand'
import { authApi, usersApi, tokensApi } from '../lib/api'

export const useStore = create((set, get) => ({
  user: null,
  profile: null,
  balance: 0,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const { data } = await authApi.login({ email, password })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ isAuthenticated: true })
      await get().fetchProfile()
    } finally {
      set({ isLoading: false })
    }
  },

  register: async (email, password, account_type) => {
    set({ isLoading: true })
    try {
      const { data } = await authApi.register({ email, password, account_type })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      set({ isAuthenticated: true })
      await get().fetchProfile()
    } finally {
      set({ isLoading: false })
    }
  },

  logout: () => {
    localStorage.clear()
    set({ user: null, profile: null, balance: 0, isAuthenticated: false })
  },

  deleteAccount: async () => {
    set({ isLoading: true })
    try {
      await authApi.deleteAccount()
      localStorage.clear()
      set({ user: null, profile: null, balance: 0, isAuthenticated: false, isLoading: false })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchProfile: async () => {
    try {
      const [profileRes, balanceRes] = await Promise.all([
        usersApi.getMe(),
        tokensApi.getBalance(),
      ])
      set({ profile: profileRes.data, balance: balanceRes.data.balance })
    } catch (e) {
      console.error('fetchProfile failed', e)
    }
  },

  setBalance: (balance) => set({ balance }),
  setProfile: (profile) => set({ profile }),
}))
