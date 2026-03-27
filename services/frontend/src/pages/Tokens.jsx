import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { tokensApi } from '../lib/api'
import { useStore } from '../store/useStore'
import { Page, SectionLabel, Spinner } from '../components/ui'

const TX_ICONS = {
  welcome:    { icon: '🎁', color: 'text-accent2' },
  contact:    { icon: '👁', color: 'text-accent' },
  payment:    { icon: '✅', color: 'text-accent2' },
  purchase:   { icon: '💳', color: 'text-gold' },
  withdrawal: { icon: '🏦', color: 'text-red-400' },
  refund:     { icon: '↩️', color: 'text-accent2' },
}

export default function TokensPage() {
  const { balance, profile } = useStore()
  const [history, setHistory] = useState(null)

  useEffect(() => {
    tokensApi.getHistory()
      .then(r => setHistory(r.data))
      .catch(() => setHistory([]))
  }, [])

  return (
    <Page>
      <div className="max-w-xl mx-auto">
        <SectionLabel>Peňaženka</SectionLabel>

        {/* Balance card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
          className="card p-8 text-center mb-6"
          style={{ background: 'linear-gradient(135deg, rgba(245,200,66,0.06), rgba(124,92,252,0.06))' }}
        >
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
            className="text-5xl mb-2"
          >🪙</motion.div>
          <div className="font-display font-black text-6xl text-gold mb-1">{balance}</div>
          <div className="text-muted text-sm">LocalMate tokenov</div>

          {profile?.account_type === 'ico' ? (
            <div className="mt-4 rounded-xl py-2.5 px-4 text-sm inline-flex items-center gap-2"
                 style={{ background: 'rgba(0,229,160,0.08)', border: '1px solid rgba(0,229,160,0.2)', color: '#00e5a0' }}>
              ✅ Živnostník — výber peňazí povolený
            </div>
          ) : (
            <div className="mt-4 rounded-xl py-2.5 px-4 text-sm inline-flex items-center gap-2"
                 style={{ background: 'rgba(122,122,154,0.08)', border: '1px solid rgba(122,122,154,0.2)', color: '#7a7a9a' }}>
              ℹ️ Výber peňazí vyžaduje IČO
            </div>
          )}
        </motion.div>

        {/* Quick info */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="card p-4 text-center">
            <div className="text-2xl font-display font-bold text-accent">5 LM</div>
            <div className="text-xs text-muted mt-1">cena za otvorenie kontaktu</div>
          </div>
          <div className="card p-4 text-center">
            <div className="text-2xl font-display font-bold text-accent2">+10 XP</div>
            <div className="text-xs text-muted mt-1">za každý dokončený gig</div>
          </div>
        </div>

        {/* Buy tokens CTA */}
        <motion.div
          whileHover={{ scale: 1.01 }}
          className="card p-5 flex items-center gap-4 mb-6 cursor-pointer"
          style={{ borderColor: 'rgba(245,200,66,0.2)' }}
        >
          <span className="text-3xl">💳</span>
          <div className="flex-1">
            <div className="font-semibold text-sm">Kúpiť tokeny</div>
            <div className="text-xs text-muted">od 2.99€ za balíček</div>
          </div>
          <span className="text-muted text-sm">Čoskoro →</span>
        </motion.div>

        {/* Transaction history */}
        <div>
          <h2 className="font-bold text-base mb-4">História transakcií</h2>
          {history === null ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : history.length === 0 ? (
            <div className="text-center py-10 text-muted text-sm">
              Zatiaľ žiadne transakcie
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {history.map((tx, i) => {
                const style = TX_ICONS[tx.tx_type] || { icon: '💱', color: 'text-muted' }
                const isPositive = tx.amount > 0
                return (
                  <motion.div
                    key={tx.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="card px-4 py-3.5 flex items-center gap-4"
                  >
                    <span className="text-2xl">{style.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{tx.description}</div>
                      <div className="text-xs text-muted">
                        {new Date(tx.created_at).toLocaleString('sk-SK')}
                      </div>
                    </div>
                    <span className={`font-display font-bold text-sm ${isPositive ? 'text-accent2' : 'text-accent'}`}>
                      {isPositive ? '+' : ''}{tx.amount} LM
                    </span>
                  </motion.div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </Page>
  )
}
