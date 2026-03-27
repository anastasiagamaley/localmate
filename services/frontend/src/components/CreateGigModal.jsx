import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { gigsApi } from '../lib/api'
import { Spinner } from './ui'

export default function CreateGigModal({ provider, clientLat, clientLon, onClose, onCreated }) {
  const [step, setStep] = useState(1)   // 1=form, 2=price check, 3=confirm, 4=done
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: '',
    price_tokens: '',
  })
  const [priceCheck, setPriceCheck] = useState(null)
  const [loading, setLoading] = useState(false)

  const handlePriceCheck = async (e) => {
    e.preventDefault()
    if (!form.title || !form.price_tokens) return
    setLoading(true)
    try {
      const { data } = await gigsApi.priceCheck({
        title: form.title,
        description: form.description,
        proposed_price: parseInt(form.price_tokens),
      })
      setPriceCheck(data)
      setStep(2)
    } catch {
      toast.error('Nepodarilo sa skontrolovať cenu')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    setLoading(true)
    try {
      await gigsApi.create({
        provider_id: provider.user_id,
        title: form.title,
        description: form.description,
        category: form.category,
        price_tokens: parseInt(form.price_tokens),
        recommended_min: priceCheck?.recommended_min || 0,
        recommended_max: priceCheck?.recommended_max || 0,
        client_lat: clientLat || null,
        client_lon: clientLon || null,
      })
      setStep(3)
      onCreated?.()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Nepodarilo sa vytvoriť gig')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="card p-8 w-full max-w-md relative"
        style={{ maxHeight: '90vh', overflowY: 'auto' }}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-5 text-muted hover:text-text text-2xl leading-none"
        >×</button>

        {/* Step 1 — Form */}
        {step === 1 && (
          <form onSubmit={handlePriceCheck}>
            <h2 className="font-display font-black text-2xl mb-1">Vytvoriť gig</h2>
            <p className="text-muted text-sm mb-6">
              Pre: <strong className="text-text">{provider.name || 'Poskytovateľ'}</strong>
              {' · '}{provider.service_description?.slice(0, 40)}
            </p>

            <div className="flex flex-col gap-4">
              <div>
                <label className="label">Názov práce</label>
                <input className="input" placeholder="Napr. Oprava displeja iPhone 13"
                  value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
                  required />
              </div>
              <div>
                <label className="label">Popis (voliteľné)</label>
                <textarea className="input resize-none h-20"
                  placeholder="Detaily, čo presne treba urobiť..."
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })} />
              </div>
              <div>
                <label className="label">Tvoja navrhovaná cena (LM tokeny)</label>
                <input className="input" type="number" min="1" placeholder="Napr. 150"
                  value={form.price_tokens}
                  onChange={e => setForm({ ...form, price_tokens: e.target.value })}
                  required />
                <p className="text-xs text-muted mt-1">
                  AI skontroluje či je cena férová pred odoslaním
                </p>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                type="submit" disabled={loading}
                className="btn-primary py-3 text-base flex items-center justify-center gap-2"
              >
                {loading ? <><Spinner size={18} /> Kontrolujem cenu...</> : '🤖 Skontrolovať cenu →'}
              </motion.button>
            </div>
          </form>
        )}

        {/* Step 2 — Price check result */}
        {step === 2 && priceCheck && (
          <div>
            <h2 className="font-display font-black text-2xl mb-6">Kontrola ceny</h2>

            {/* Recommended range */}
            <div className="card p-4 mb-4"
                 style={{ background: 'rgba(0,229,160,0.05)', borderColor: 'rgba(0,229,160,0.2)' }}>
              <p className="text-xs text-muted mb-1 uppercase tracking-wide font-bold">AI odporúčanie</p>
              <p className="font-display font-bold text-2xl text-accent2">
                {priceCheck.recommended_min} – {priceCheck.recommended_max} LM
              </p>
              <p className="text-xs text-muted mt-1">{priceCheck.ai_explanation}</p>
            </div>

            {/* User's price */}
            <div className="card p-4 mb-4"
                 style={{
                   borderColor: priceCheck.is_reasonable ? 'rgba(124,92,252,0.3)' : 'rgba(255,107,107,0.3)',
                   background: priceCheck.is_reasonable ? 'rgba(124,92,252,0.05)' : 'rgba(255,107,107,0.05)',
                 }}>
              <p className="text-xs text-muted mb-1 uppercase tracking-wide font-bold">Tvoja cena</p>
              <p className="font-display font-bold text-2xl" style={{ color: priceCheck.is_reasonable ? '#7c5cfc' : '#ff6b6b' }}>
                {priceCheck.proposed_price} LM
              </p>
              <p className="text-xs mt-1" style={{ color: priceCheck.is_reasonable ? '#00e5a0' : '#ff6b6b' }}>
                {priceCheck.is_reasonable ? '✅ Cena je v poriadku' : '⚠️ Cena je mimo odporúčaného rozsahu'}
              </p>
            </div>

            {/* Warning */}
            {priceCheck.warning && (
              <div className="rounded-xl p-3 text-sm mb-4"
                   style={{ background: 'rgba(255,107,107,0.08)', border: '1px solid rgba(255,107,107,0.2)', color: '#ff6b6b' }}>
                ⚠️ {priceCheck.warning}
                {!priceCheck.is_reasonable && (
                  <p className="mt-1 text-xs opacity-80">
                    Gig bude označený a skontrolovaný administrátorom pred spustením.
                  </p>
                )}
              </div>
            )}

            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                onClick={() => setStep(1)}
                className="btn-ghost flex-1 py-3"
              >
                ← Zmeniť cenu
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                onClick={handleCreate} disabled={loading}
                className="btn-primary flex-1 py-3 flex items-center justify-center gap-2"
              >
                {loading ? <Spinner size={18} /> : null}
                {priceCheck.is_reasonable ? 'Vytvoriť gig ✅' : 'Odoslať na kontrolu'}
              </motion.button>
            </div>
          </div>
        )}

        {/* Step 3 — Success */}
        {step === 3 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-4"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.1 }}
              className="text-6xl mb-4"
            >🎉</motion.div>
            <h2 className="font-display font-black text-2xl mb-2">Gig vytvorený!</h2>
            <p className="text-muted text-sm mb-6">
              Poskytovateľ dostane notifikáciu a môže gig prijať.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              onClick={onClose}
              className="btn-primary w-full py-3"
            >
              Zavrieť
            </motion.button>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}
