import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { usersApi } from '../lib/api'
import { useStore } from '../store/useStore'
import { Page, SectionLabel, LevelBadge, XpBar, Spinner } from '../components/ui'

export default function ProfilePage() {
  const { profile, setProfile, fetchProfile, deleteAccount } = useStore()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [xpData, setXpData] = useState(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [form, setForm] = useState({
    name: '', bio: '', city: '',
    service_description: '', tags: '',
    lat: '', lon: '',
  })
  const [saving, setSaving] = useState(false)

  const handleDeleteAccount = async () => {
    setDeleting(true)
    try {
      await deleteAccount()
      toast.success('Účet bol zmazaný')
      navigate('/')
    } catch (e) {
      toast.error('Nepodarilo sa zmazať účet')
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  useEffect(() => {
    if (profile) {
      setForm({
        name: profile.name || '',
        bio: profile.bio || '',
        city: profile.city || '',
        service_description: profile.service_description || '',
        tags: profile.tags || '',
        lat: '', lon: '',
      })
      // fetch XP details
      usersApi.getXp(profile.user_id)
        .then(r => setXpData(r.data))
        .catch(() => {})
    }
  }, [profile])

  const useMyLocation = () => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm(f => ({
          ...f,
          lat: pos.coords.latitude.toFixed(6),
          lon: pos.coords.longitude.toFixed(6),
        }))
        toast.success('Poloha aktualizovaná ✅')
      },
      () => toast.error('Nepodarilo sa zistiť polohu')
    )
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        name: form.name,
        bio: form.bio,
        city: form.city,
        service_description: form.service_description,
        tags: form.tags,
      }
      if (form.lat && form.lon) {
        payload.lat = parseFloat(form.lat)
        payload.lon = parseFloat(form.lon)
      }
      const { data } = await usersApi.updateMe(payload)
      setProfile(data)
      setEditing(false)
      toast.success('Profil uložený!')
    } catch {
      toast.error('Nepodarilo sa uložiť profil')
    } finally {
      setSaving(false)
    }
  }

  if (!profile) {
    return (
      <Page>
        <div className="flex justify-center pt-20"><Spinner size={36} /></div>
      </Page>
    )
  }

  return (
    <Page>
      <div className="max-w-2xl mx-auto">
        <SectionLabel>Môj profil</SectionLabel>

        {/* ── Header card ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          className="card p-6 mb-5"
        >
          <div className="flex items-start gap-5 mb-6">
            {/* Avatar */}
            <div className="w-16 h-16 rounded-full flex items-center justify-center text-3xl flex-shrink-0"
                 style={{ background: 'linear-gradient(135deg,#7c5cfc,#c084fc)' }}>
              🧑
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1 flex-wrap">
                <h1 className="font-display font-black text-2xl tracking-tight">
                  {profile.name || 'Bez mena'}
                </h1>
                <LevelBadge level={profile.level} levelName={profile.level_name} />
              </div>
              <p className="text-sm text-muted">{profile.city || 'Lokalita nenastavená'}</p>
              <p className="text-xs text-muted mt-1">
                {profile.account_type === 'ico' ? '✅ Živnostník (výber peňazí povolený)' : 'ℹ️ Bežný účet'}
              </p>
            </div>
            <motion.button
              whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
              onClick={() => setEditing(!editing)}
              className="btn-ghost text-sm py-2 px-4"
            >
              {editing ? 'Zrušiť' : '✏️ Upraviť'}
            </motion.button>
          </div>

          {/* XP Bar */}
          {xpData && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-muted uppercase tracking-wide">
                  Progres — {xpData.gigs_completed} gigov dokončených
                </span>
              </div>
              <XpBar
                xp={xpData.xp}
                level={xpData.level}
                gigs_completed={xpData.gigs_completed}
                xp_to_next_level={xpData.xp_to_next_level}
              />
            </div>
          )}
        </motion.div>

        {/* ── Stats row ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-3 gap-3 mb-5"
        >
          {[
            { label: 'Level', value: profile.level, sub: profile.level_name },
            { label: 'XP', value: xpData?.xp ?? '—', sub: 'bodov celkom' },
            { label: 'Gigy', value: profile.gigs_completed, sub: 'dokončených' },
          ].map((s) => (
            <div key={s.label} className="card p-4 text-center">
              <div className="font-display font-black text-3xl">{s.value}</div>
              <div className="text-xs text-muted mt-1">{s.sub}</div>
            </div>
          ))}
        </motion.div>

        {/* ── Profile info (view mode) ── */}
        {!editing && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="card p-6 flex flex-col gap-4"
          >
            <Section label="Bio" value={profile.bio || '—'} />
            <Section label="Čo ponúkam" value={profile.service_description || 'Nenastavené'} />
            <div>
              <p className="label mb-2">Tagy</p>
              <div className="flex flex-wrap gap-2">
                {profile.tags
                  ? profile.tags.split(',').filter(Boolean).map(t => (
                      <span key={t}
                        className="text-xs border border-border rounded-full px-3 py-1 text-muted">
                        {t.trim()}
                      </span>
                    ))
                  : <span className="text-muted text-sm">—</span>
                }
              </div>
            </div>
            {!profile.city && (
              <div className="rounded-xl p-4 text-sm"
                   style={{ background: 'rgba(245,200,66,0.08)', border: '1px solid rgba(245,200,66,0.2)' }}>
                ⚠️ Nastav svoju <strong className="text-gold">polohu</strong> a <strong className="text-gold">popis služby</strong> — bez toho ťa AI nevie nájsť!
              </div>
            )}
          </motion.div>
        )}

        {/* ── Edit form ── */}
        {editing && (
          <motion.form
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            onSubmit={handleSave}
            className="card p-6 flex flex-col gap-5"
          >
            <div>
              <label className="label">Meno</label>
              <input className="input" placeholder="Tvoje meno"
                value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <label className="label">Bio</label>
              <textarea className="input resize-none h-20" placeholder="Pár viet o sebe..."
                value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} />
            </div>
            <div>
              <label className="label">Mesto</label>
              <input className="input" placeholder="Bratislava, Košice..."
                value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} />
            </div>
            <div>
              <label className="label">Čo ponúkam (popis pre AI)</label>
              <textarea className="input resize-none h-24"
                placeholder="Napr. Opravujem smartfóny iPhone a Android, vymieňam displeje a batérie..."
                value={form.service_description}
                onChange={e => setForm({ ...form, service_description: e.target.value })} />
            </div>
            <div>
              <label className="label">Tagy (čiarkou oddelené)</label>
              <input className="input" placeholder="oprava,iPhone,Android,displej"
                value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} />
            </div>

            {/* Location */}
            <div>
              <label className="label">GPS poloha</label>
              <div className="flex gap-2">
                <input className="input" placeholder="Šírka: 48.1486"
                  value={form.lat} onChange={e => setForm({ ...form, lat: e.target.value })} />
                <input className="input" placeholder="Dĺžka: 17.1077"
                  value={form.lon} onChange={e => setForm({ ...form, lon: e.target.value })} />
                <motion.button type="button" whileHover={{ scale: 1.04 }}
                  onClick={useMyLocation}
                  className="btn-ghost text-sm px-3 flex-shrink-0">
                  📍
                </motion.button>
              </div>
              <p className="text-xs text-muted mt-1">
                Poloha je potrebná na zobrazenie vo výsledkoch vyhľadávania
              </p>
            </div>

            <motion.button
              whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
              type="submit" disabled={saving}
              className="btn-primary py-3 text-base"
            >
              {saving ? 'Ukladám...' : 'Uložiť profil'}
            </motion.button>
          </motion.form>
        )}

        {/* ── Danger zone ── */}
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="card p-6 mt-5"
          style={{ borderColor: 'rgba(255,107,107,0.2)' }}
        >
          <h3 className="font-bold text-sm mb-1" style={{ color: '#ff6b6b' }}>⚠️ Nebezpečná zóna</h3>
          <p className="text-muted text-xs mb-4">
            Po zmazaní účtu stratíš prístup ku všetkým dátam a tokenom. Táto akcia je nevratná.
          </p>

          {!showDeleteConfirm ? (
            <motion.button
              whileHover={{ scale: 1.02 }}
              onClick={() => setShowDeleteConfirm(true)}
              className="btn-ghost text-sm py-2 px-4"
              style={{ borderColor: 'rgba(255,107,107,0.3)', color: '#ff6b6b' }}
            >
              🗑 Zmazať účet
            </motion.button>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              className="rounded-xl p-4"
              style={{ background: 'rgba(255,107,107,0.06)', border: '1px solid rgba(255,107,107,0.2)' }}
            >
              <p className="text-sm font-semibold mb-3" style={{ color: '#ff6b6b' }}>
                Si si istá? Toto nejde vrátiť.
              </p>
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  onClick={handleDeleteAccount}
                  disabled={deleting}
                  className="btn-primary text-sm py-2 px-4"
                  style={{ background: '#ff6b6b' }}
                >
                  {deleting ? 'Mažem...' : 'Áno, zmazať účet'}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  onClick={() => setShowDeleteConfirm(false)}
                  className="btn-ghost text-sm py-2 px-4"
                >
                  Zrušiť
                </motion.button>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </Page>
  )
}

function Section({ label, value }) {
  return (
    <div>
      <p className="label">{label}</p>
      <p className="text-sm leading-relaxed">{value}</p>
    </div>
  )
}
