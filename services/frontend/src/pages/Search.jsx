import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { searchApi, tokensApi } from '../lib/api'
import { useStore } from '../store/useStore'
import { Page, SectionLabel, LevelBadge, Spinner } from '../components/ui'
import { Search, MapPin, Coins } from 'lucide-react'

export default function SearchPage() {
  const { balance, setBalance } = useStore()
  const [query, setQuery] = useState('')
  const [lat, setLat] = useState('')
  const [lon, setLon] = useState('')
  const [results, setResults] = useState(null)
  const [interpreted, setInterpreted] = useState(null)
  const [loading, setLoading] = useState(false)
  const [openedContacts, setOpenedContacts] = useState(new Set())

  const useMyLocation = () => {
    if (!navigator.geolocation) { toast.error('Geolokácia nie je dostupná'); return }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6))
        setLon(pos.coords.longitude.toFixed(6))
        toast.success('Poloha zistená ✅')
      },
      () => toast.error('Nepodarilo sa zistiť polohu')
    )
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    if (!lat || !lon) { toast.error('Zadaj svoju polohu'); return }

    setLoading(true)
    setResults(null)
    try {
      const { data } = await searchApi.search({
        query,
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        max_distance_km: 20,
        limit: 10,
      })
      setResults(data.results)
      setInterpreted(data.interpreted)
    } catch (err) {
      toast.error('Vyhľadávanie zlyhalo. Skúste znova.')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenContact = async (userId) => {
    try {
      const { data } = await tokensApi.openContact({ target_user_id: userId })
      setBalance(data.new_balance)
      setOpenedContacts(prev => new Set([...prev, userId]))
      toast.success(`Kontakt otvorený! −5 LM | Zostatok: ${data.new_balance} LM`)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Nepodarilo sa otvoriť kontakt'
      toast.error(msg)
    }
  }

  return (
    <Page>
      <SectionLabel>AI vyhľadávanie</SectionLabel>
      <h1 className="font-display font-black text-4xl tracking-tight mb-8">
        Čo hľadáš?
      </h1>

      {/* Search form */}
      <motion.form
        onSubmit={handleSearch}
        className="card p-6 mb-8"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex flex-col gap-4">
          <div>
            <label className="label">Čo potrebuješ?</label>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted" size={16} />
              <input
                className="input pl-11"
                placeholder="Napr. Potrebujem inštalatéra dnes večer, urgentne..."
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 items-end">
            <div>
              <label className="label">Zemepisná šírka</label>
              <input className="input" placeholder="48.1486" value={lat}
                onChange={e => setLat(e.target.value)} />
            </div>
            <div>
              <label className="label">Zemepisná dĺžka</label>
              <input className="input" placeholder="17.1077" value={lon}
                onChange={e => setLon(e.target.value)} />
            </div>
            <motion.button
              type="button" whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              onClick={useMyLocation}
              className="btn-ghost flex items-center justify-center gap-2 py-3"
            >
              <MapPin size={15} /> Moja poloha
            </motion.button>
          </div>

          <motion.button
            type="submit" whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
            disabled={loading}
            className="btn-green py-3.5 text-base flex items-center justify-center gap-2"
          >
            {loading ? <><Spinner size={18} /> AI hľadá...</> : '🤖 Hľadať s AI'}
          </motion.button>
        </div>
      </motion.form>

      {/* AI interpretation */}
      <AnimatePresence>
        {interpreted && !loading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex items-center gap-2 mb-4 text-sm text-muted"
          >
            <span className="w-2 h-2 rounded-full bg-accent2 animate-pulse" />
            AI pochopil: <span className="text-text font-semibold">
              {interpreted.summary || query}
            </span>
            {interpreted.urgency === 'now' && (
              <span className="text-xs text-red-400 font-bold border border-red-400/30
                             bg-red-400/10 px-2 py-0.5 rounded-full ml-1">URGENTNÉ</span>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading skeleton */}
      {loading && (
        <div className="flex flex-col gap-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="flex gap-4">
                <div className="w-12 h-12 rounded-full bg-border" />
                <div className="flex-1 flex flex-col gap-2">
                  <div className="h-4 bg-border rounded w-1/3" />
                  <div className="h-3 bg-border rounded w-2/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {results && !loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {results.length === 0 ? (
              <div className="text-center py-16 text-muted">
                <div className="text-5xl mb-4">🔍</div>
                <p className="font-semibold">Žiadne výsledky v okolí</p>
                <p className="text-sm mt-1">Skús iný dopyt alebo väčší rádius</p>
              </div>
            ) : (
              <>
                <p className="text-sm text-muted mb-4">
                  Nájdených <strong className="text-text">{results.length}</strong> poskytovateľov
                </p>
                <div className="flex flex-col gap-3">
                  {results.map((r, i) => (
                    <ResultCard
                      key={r.user_id}
                      result={r}
                      rank={i + 1}
                      opened={openedContacts.has(r.user_id)}
                      onOpen={() => handleOpenContact(r.user_id)}
                    />
                  ))}
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Page>
  )
}

function ResultCard({ result: r, rank, opened, onOpen }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.06 }}
      whileHover={{ borderColor: 'rgba(124,92,252,0.4)' }}
      className="card p-5 flex items-center gap-5 transition-colors duration-200"
    >
      {/* Rank */}
      <div className="font-display font-black text-3xl text-border w-8 text-center select-none">
        {rank}
      </div>

      {/* Avatar */}
      <div className="w-12 h-12 rounded-full flex items-center justify-center text-xl flex-shrink-0"
           style={{ background: 'linear-gradient(135deg,#7c5cfc,#c084fc)' }}>
        🧑
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-bold">{r.name || 'Používateľ'}</span>
          <LevelBadge level={r.level} levelName={r.level_name} small />
        </div>
        <p className="text-sm text-muted truncate">{r.service_description}</p>
        <div className="flex gap-2 mt-1.5 flex-wrap">
          {r.tags.split(',').filter(Boolean).slice(0, 3).map(tag => (
            <span key={tag} className="text-xs border border-border rounded-full px-2 py-0.5 text-muted">
              {tag.trim()}
            </span>
          ))}
        </div>
      </div>

      {/* Distance */}
      <div className="text-xs font-bold text-accent2 bg-accent2/10 px-3 py-1.5 rounded-full flex-shrink-0">
        {r.distance_km} km
      </div>

      {/* Contact button */}
      <div className="flex-shrink-0">
        {opened ? (
          <motion.div
            initial={{ scale: 0.8 }} animate={{ scale: 1 }}
            className="text-sm font-bold text-accent2 bg-accent2/10 border border-accent2/30
                       rounded-xl px-4 py-2.5"
          >
            ✅ Kontakt otvorený
          </motion.div>
        ) : (
          <motion.button
            whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
            onClick={onOpen}
            className="btn-primary text-sm flex items-center gap-1.5 py-2.5 px-4"
          >
            👁 Otvoriť <span className="text-accent/70 font-normal">−5 🪙</span>
          </motion.button>
        )}
      </div>
    </motion.div>
  )
}
