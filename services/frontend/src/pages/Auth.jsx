import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { useStore } from '../store/useStore'
import { Page } from '../components/ui'

// ─── Login ────────────────────────────────────────────────────────────────────
export function Login() {
  const navigate = useNavigate()
  const { login, isLoading } = useStore()
  const [form, setForm] = useState({ email: '', password: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(form.email, form.password)
      toast.success('Vitaj späť!')
      navigate('/search')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Nesprávny email alebo heslo')
    }
  }

  return (
    <Page>
      <div className="max-w-md mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-8"
        >
          <h1 className="font-display font-black text-3xl tracking-tight mb-2">Prihlásiť sa</h1>
          <p className="text-muted text-sm mb-8">Vitaj späť v LocalMate</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" placeholder="tvoj@email.sk"
                value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
            </div>
            <div>
              <label className="label">Heslo</label>
              <input className="input" type="password" placeholder="••••••••"
                value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              type="submit" disabled={isLoading}
              className="btn-primary w-full py-3 text-base mt-2"
            >
              {isLoading ? 'Prihlasujem...' : 'Prihlásiť sa'}
            </motion.button>
          </form>

          <p className="text-center text-muted text-sm mt-6">
            Nemáš účet?{' '}
            <Link to="/register" className="text-accent hover:underline font-semibold">
              Registrovať sa
            </Link>
          </p>
        </motion.div>
      </div>
    </Page>
  )
}

// ─── Register ─────────────────────────────────────────────────────────────────
export function Register() {
  const navigate = useNavigate()
  const { register: reg, isLoading } = useStore()
  const [form, setForm] = useState({ email: '', password: '', account_type: 'regular' })
  const [step, setStep] = useState(1) // 1=credentials, 2=success

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password.length < 8) {
      toast.error('Heslo musí mať aspoň 8 znakov')
      return
    }
    try {
      await reg(form.email, form.password, form.account_type)
      setStep(2)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registrácia zlyhala')
    }
  }

  if (step === 2) {
    return (
      <Page>
        <div className="max-w-md mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card p-8 text-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.1 }}
              className="text-6xl mb-4"
            >🎉</motion.div>
            <h2 className="font-display font-black text-3xl mb-2">Hotovo!</h2>
            <p className="text-muted text-sm mb-6">Vitaj v LocalMate. Tvoje tokeny sú na účte!</p>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="rounded-2xl p-5 mb-4"
              style={{ background: 'rgba(245,200,66,0.08)', border: '1px solid rgba(245,200,66,0.2)' }}
            >
              <div className="font-display font-black text-4xl text-gold">🪙 50 LM</div>
              <div className="text-sm text-muted mt-1">Uvítací bonus pridaný na účet</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="rounded-xl p-4 mb-6 text-sm"
              style={{ background: 'rgba(124,92,252,0.08)', border: '1px solid rgba(124,92,252,0.2)' }}
            >
              🎮 Štartuješ ako <strong className="text-yellow-600">🥉 Bronzový · Level 1</strong>
              <br />Dokonči prvý gig a získaj +10 XP!
            </motion.div>

            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/profile')}
              className="btn-primary w-full py-3 text-base"
            >
              Nastaviť profil →
            </motion.button>
          </motion.div>
        </div>
      </Page>
    )
  }

  return (
    <Page>
      <div className="max-w-md mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-8"
        >
          <h1 className="font-display font-black text-3xl tracking-tight mb-2">Pridaj sa</h1>
          <p className="text-muted text-sm mb-6">Vytvor profil za 30 sekúnd</p>

          {/* Gift banner */}
          <div className="rounded-xl p-4 flex items-center gap-3 mb-6"
               style={{ background: 'rgba(245,200,66,0.08)', border: '1px solid rgba(245,200,66,0.2)' }}>
            <span className="text-3xl">🎁</span>
            <div className="text-sm">
              Pri registrácii dostaneš <strong className="text-gold">50 tokenov</strong> zadarmo — stačí na 10 kontaktov!
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" placeholder="tvoj@email.sk"
                value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
            </div>
            <div>
              <label className="label">Heslo (min. 8 znakov)</label>
              <input className="input" type="password" placeholder="••••••••"
                value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
            </div>
            <div>
              <label className="label">Typ účtu</label>
              <select className="input cursor-pointer"
                value={form.account_type}
                onChange={e => setForm({ ...form, account_type: e.target.value })}
              >
                <option value="regular">Bežný používateľ (bez IČO)</option>
                <option value="ico">Živnostník / s.r.o. (s IČO)</option>
              </select>
              <p className="text-xs text-muted mt-1.5">
                {form.account_type === 'ico'
                  ? '✅ Môžeš vyberať peniaze na bankový účet'
                  : 'ℹ️ Môžeš zarábať tokeny, ale výber na účet nie je dostupný bez IČO'}
              </p>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              type="submit" disabled={isLoading}
              className="btn-primary w-full py-3 text-base mt-2"
            >
              {isLoading ? 'Registrujem...' : 'Registrovať sa → +50 🪙'}
            </motion.button>
          </form>

          <p className="text-center text-muted text-sm mt-6">
            Máš účet?{' '}
            <Link to="/login" className="text-accent hover:underline font-semibold">
              Prihlásiť sa
            </Link>
          </p>
        </motion.div>
      </div>
    </Page>
  )
}
