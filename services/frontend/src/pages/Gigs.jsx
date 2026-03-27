import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { gigsApi } from '../lib/api'
import { Page, SectionLabel, Spinner } from '../components/ui'
import { useStore } from '../store/useStore'

const STATUS_LABEL = {
  pending:   { text: 'Čaká na prijatie', color: '#f5c842',  bg: 'rgba(245,200,66,0.1)'  },
  accepted:  { text: 'Prebieha',         color: '#7c5cfc',  bg: 'rgba(124,92,252,0.1)'  },
  completed: { text: 'Dokončený',        color: '#00e5a0',  bg: 'rgba(0,229,160,0.1)'   },
  cancelled: { text: 'Zrušený',          color: '#7a7a9a',  bg: 'rgba(122,122,154,0.1)' },
  flagged:   { text: 'Preveruje sa',     color: '#ff6b6b',  bg: 'rgba(255,107,107,0.1)' },
  disputed:  { text: 'Spor',             color: '#ff6b6b',  bg: 'rgba(255,107,107,0.1)' },
}

export default function GigsPage() {
  const { profile, fetchProfile } = useStore()
  const [gigs, setGigs] = useState(null)
  const [filter, setFilter] = useState('all')
  const [selectedGig, setSelectedGig] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadGigs() }, [filter])

  const loadGigs = async () => {
    setLoading(true)
    try {
      const { data } = await gigsApi.myGigs(filter === 'all' ? null : filter)
      setGigs(data)
    } catch {
      toast.error('Nepodarilo sa načítať gigy')
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async (gigId) => {
    try {
      await gigsApi.accept(gigId)
      toast.success('Gig prijatý! ✅')
      loadGigs()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Chyba')
    }
  }

  const handleComplete = async (gigId) => {
    try {
      await gigsApi.complete(gigId)
      toast.success('Gig dokončený! Tokeny prevedené 🎉')
      fetchProfile()
      loadGigs()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Chyba')
    }
  }

  const handleCancel = async (gigId) => {
    if (!window.confirm('Naozaj chceš zrušiť tento gig?')) return
    try {
      await gigsApi.cancel(gigId, 'Zrušené používateľom')
      toast.success('Gig zrušený')
      loadGigs()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Chyba')
    }
  }

  const FILTERS = [
    { key: 'all',       label: 'Všetky' },
    { key: 'pending',   label: 'Čakajúce' },
    { key: 'accepted',  label: 'Prebiehajúce' },
    { key: 'completed', label: 'Dokončené' },
  ]

  return (
    <Page>
      <SectionLabel>Moje gigy</SectionLabel>
      <h1 className="font-display font-black text-4xl tracking-tight mb-8">Gigy</h1>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
              filter === f.key
                ? 'border-accent text-text'
                : 'border-border text-muted hover:border-accent/50'
            }`}
            style={filter === f.key ? { background: 'rgba(124,92,252,0.1)' } : { background: 'transparent' }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="flex justify-center py-16"><Spinner size={36} /></div>
      ) : gigs?.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="text-5xl mb-4">📋</div>
          <p className="font-semibold text-lg mb-2">Žiadne gigy</p>
          <p className="text-muted text-sm">Nájdi niekoho cez vyhľadávanie a vytvor prvý gig</p>
        </motion.div>
      ) : (
        <div className="flex flex-col gap-3">
          {gigs?.map((gig, i) => (
            <GigCard
              key={gig.id}
              gig={gig}
              myId={profile?.user_id}
              index={i}
              onAccept={() => handleAccept(gig.id)}
              onComplete={() => handleComplete(gig.id)}
              onCancel={() => handleCancel(gig.id)}
              onExpand={() => setSelectedGig(selectedGig?.id === gig.id ? null : gig)}
              expanded={selectedGig?.id === gig.id}
            />
          ))}
        </div>
      )}
    </Page>
  )
}

function GigCard({ gig, myId, index, onAccept, onComplete, onCancel, onExpand, expanded }) {
  const s = STATUS_LABEL[gig.status] || STATUS_LABEL.pending
  const isClient   = gig.client_id === myId
  const isProvider = gig.provider_id === myId

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="card overflow-hidden"
    >
      {/* Header row */}
      <div
        className="p-5 flex items-center gap-4 cursor-pointer"
        onClick={onExpand}
      >
        {/* Role badge */}
        <div
          className="text-xs font-bold px-2.5 py-1 rounded-lg border flex-shrink-0"
          style={{
            color: isClient ? '#7c5cfc' : '#00e5a0',
            borderColor: isClient ? 'rgba(124,92,252,0.3)' : 'rgba(0,229,160,0.3)',
            background: isClient ? 'rgba(124,92,252,0.08)' : 'rgba(0,229,160,0.08)',
          }}
        >
          {isClient ? '👤 Klient' : '🔧 Poskytovateľ'}
        </div>

        <div className="flex-1 min-w-0">
          <div className="font-bold truncate">{gig.title}</div>
          <div className="text-sm text-muted mt-0.5">
            {new Date(gig.created_at).toLocaleDateString('sk-SK')}
          </div>
        </div>

        {/* Price */}
        <div className="font-display font-bold text-gold text-sm flex-shrink-0">
          🪙 {gig.price_tokens} LM
        </div>

        {/* Status */}
        <div
          className="text-xs font-bold px-2.5 py-1 rounded-lg flex-shrink-0"
          style={{ color: s.color, background: s.bg }}
        >
          {s.text}
        </div>

        <div className="text-muted text-sm">{expanded ? '▲' : '▼'}</div>
      </div>

      {/* Expanded details + actions */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 border-t border-border pt-4 flex flex-col gap-4">
              {gig.description && (
                <p className="text-sm text-muted leading-relaxed">{gig.description}</p>
              )}

              {/* Flagged warning */}
              {gig.price_flagged && (
                <div className="rounded-xl p-3 text-sm"
                     style={{ background: 'rgba(255,107,107,0.08)', border: '1px solid rgba(255,107,107,0.2)', color: '#ff6b6b' }}>
                  ⚠️ {gig.flag_reason || 'Gig sa preveruje pre podozrivú cenu'}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-2 flex-wrap">

                {/* Provider can accept pending gig */}
                {isProvider && gig.status === 'pending' && (
                  <motion.button
                    whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    onClick={onAccept}
                    className="btn-green text-sm px-5 py-2.5"
                  >
                    ✅ Prijať gig
                  </motion.button>
                )}

                {/* Client can confirm completion */}
                {isClient && gig.status === 'accepted' && (
                  <motion.button
                    whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    onClick={onComplete}
                    className="btn-green text-sm px-5 py-2.5"
                  >
                    🎉 Potvrdiť dokončenie → zaplatiť {gig.price_tokens} 🪙
                  </motion.button>
                )}

                {/* Cancel — both can cancel if not done */}
                {!['completed', 'cancelled'].includes(gig.status) && (
                  <motion.button
                    whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    onClick={onCancel}
                    className="btn-ghost text-sm px-5 py-2.5"
                    style={{ borderColor: 'rgba(255,107,107,0.3)', color: '#ff6b6b' }}
                  >
                    ✕ Zrušiť
                  </motion.button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
