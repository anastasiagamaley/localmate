import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { useStore } from '../store/useStore'
import { LogOut, Search, User, Coins } from 'lucide-react'

// ─── Navbar ───────────────────────────────────────────────────────────────────
export function Navbar() {
  const { isAuthenticated, profile, balance, logout } = useStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="sticky top-0 z-50 border-b border-border backdrop-blur-xl"
      style={{ background: 'rgba(10,10,15,0.88)' }}
    >
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="font-display font-black text-xl tracking-tight">
          Local<span className="text-accent">Mate</span>
        </Link>

        <div className="flex items-center gap-3">
          {isAuthenticated ? (
            <>
              {/* Token balance */}
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="flex items-center gap-1.5 bg-surface border border-border
                           rounded-xl px-3 py-1.5 text-sm font-bold text-gold cursor-pointer"
                onClick={() => navigate('/tokens')}
              >
                <span>🪙</span>
                <span>{balance} LM</span>
              </motion.div>

              {/* Level badge */}
              {profile && (
                <LevelBadge level={profile.level} levelName={profile.level_name} small />
              )}

              <motion.button
                whileHover={{ scale: 1.05 }}
                onClick={() => navigate('/search')}
                className="btn-primary flex items-center gap-2 text-sm py-2 px-4"
              >
                <Search size={15} />
                Hľadať
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                onClick={() => navigate('/gigs')}
                className="btn-ghost flex items-center gap-2 text-sm py-2 px-4"
              >
                📋 Gigy
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                onClick={() => navigate('/profile')}
                className="btn-ghost flex items-center gap-2 text-sm py-2 px-4"
              >
                <User size={15} />
                Profil
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                onClick={handleLogout}
                className="text-muted hover:text-text transition-colors p-2 rounded-lg
                           hover:bg-surface"
                title="Odhlásiť sa"
              >
                <LogOut size={16} />
              </motion.button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost text-sm py-2 px-4">Prihlásiť sa</Link>
              <Link to="/register" className="btn-primary text-sm py-2 px-4">Registrovať sa</Link>
            </>
          )}
        </div>
      </div>
    </motion.nav>
  )
}

// ─── Level Badge ──────────────────────────────────────────────────────────────
const LEVEL_STYLES = {
  1: { color: '#cd7f32', bg: 'rgba(205,127,50,0.12)', border: 'rgba(205,127,50,0.35)', icon: '🥉' },
  2: { color: '#a8b8c8', bg: 'rgba(168,184,200,0.12)', border: 'rgba(168,184,200,0.35)', icon: '🥈' },
  3: { color: '#f5c842', bg: 'rgba(245,200,66,0.12)', border: 'rgba(245,200,66,0.35)', icon: '🏅' },
  4: { color: '#f5c842', bg: 'rgba(245,200,66,0.12)', border: 'rgba(245,200,66,0.35)', icon: '🏅' },
  5: { color: '#7c5cfc', bg: 'rgba(124,92,252,0.12)', border: 'rgba(124,92,252,0.35)', icon: '💎' },
  6: { color: '#7c5cfc', bg: 'rgba(124,92,252,0.12)', border: 'rgba(124,92,252,0.35)', icon: '💎' },
  7: { color: '#7c5cfc', bg: 'rgba(124,92,252,0.12)', border: 'rgba(124,92,252,0.35)', icon: '💎' },
  8: { color: '#00e5a0', bg: 'rgba(0,229,160,0.12)', border: 'rgba(0,229,160,0.35)', icon: '👑' },
}

export function LevelBadge({ level = 1, levelName = '', small = false }) {
  const s = LEVEL_STYLES[level] || LEVEL_STYLES[1]
  return (
    <span
      className="level-badge"
      style={{ color: s.color, background: s.bg, borderColor: s.border,
               fontSize: small ? '11px' : '12px' }}
    >
      {s.icon} {small ? `Lv.${level}` : levelName}
    </span>
  )
}

// ─── XP Progress Bar ──────────────────────────────────────────────────────────
const NEXT_LEVEL_AT = [0, 10, 30, 100, 100, 300, 300, 300, Infinity]

export function XpBar({ xp, level, gigs_completed, xp_to_next_level }) {
  const nextAt = NEXT_LEVEL_AT[level] || 300
  const prevAt = NEXT_LEVEL_AT[level - 1] || 0
  const span = nextAt - prevAt
  const current = gigs_completed - prevAt
  const pct = span > 0 ? Math.min(100, Math.round((current / span) * 100)) : 100

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-muted mb-1.5">
        <span>{xp} XP celkom</span>
        <span>{xp_to_next_level > 0 ? `${xp_to_next_level} gigov do ďalšieho levelu` : '🏆 Max level!'}</span>
      </div>
      <div className="h-2.5 bg-surface rounded-full overflow-hidden border border-border">
        <motion.div
          className="h-full rounded-full"
          style={{ background: 'linear-gradient(90deg, #7c5cfc, #00e5a0)' }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
        />
      </div>
      <div className="text-right text-xs text-muted mt-1">{pct}%</div>
    </div>
  )
}

// ─── Page wrapper with fade animation ────────────────────────────────────────
export function Page({ children, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
      className={`max-w-6xl mx-auto px-6 py-10 ${className}`}
    >
      {children}
    </motion.div>
  )
}

// ─── Section label ────────────────────────────────────────────────────────────
export function SectionLabel({ children }) {
  return (
    <p className="text-xs font-bold tracking-widest uppercase text-accent mb-2">
      {children}
    </p>
  )
}

// ─── Spinner ─────────────────────────────────────────────────────────────────
export function Spinner({ size = 24 }) {
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 0.8, ease: 'linear' }}
      style={{ width: size, height: size,
               border: `2px solid rgba(124,92,252,0.2)`,
               borderTopColor: '#7c5cfc',
               borderRadius: '50%' }}
    />
  )
}
