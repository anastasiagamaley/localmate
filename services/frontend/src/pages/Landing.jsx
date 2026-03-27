import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Page, SectionLabel, LevelBadge } from '../components/ui'

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, delay },
})

const LEVELS = [
  { level: 1, name: 'Bronzový', req: '0–9 gigov', perks: ['Základná viditeľnosť', '+50 uvítacích tokenov'] },
  { level: 2, name: 'Strieborný 🥈', req: '10–29 gigov', perks: ['+10% viditeľnosť', 'Overený odznak'] },
  { level: 3, name: 'Zlatý 🏅', req: '30–99 gigov', perks: ['Priorita vo výsledkoch', 'Zľava na kontakt'] },
  { level: 5, name: 'Platinový 💎', req: '100–299 gigov', perks: ['Vlastná stránka', 'Top výber v okolí'] },
  { level: 8, name: 'Master 👑', req: '300+ gigov', perks: ['#1 v meste', 'Mentoring nováčikov'] },
]

export default function Landing() {
  return (
    <div>
      {/* ── Hero ── */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-16 grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
        <div>
          <motion.div {...fadeUp(0)}
            className="inline-flex items-center gap-2 text-xs font-bold text-accent
                       bg-accent/10 border border-accent/30 rounded-full px-3 py-1.5 mb-6"
          >
            <span className="w-2 h-2 rounded-full bg-accent2 animate-pulse" />
            Aktívna lokálna sieť · Slovensko
          </motion.div>

          <motion.h1 {...fadeUp(0.1)}
            className="font-display font-black text-5xl leading-tight tracking-tighter mb-6"
          >
            Nájdi čo potrebuješ
            <br /><span className="text-accent">vo svojom okolí</span>
            <br />hneď <span className="text-accent2">teraz</span>
          </motion.h1>

          <motion.p {...fadeUp(0.2)} className="text-muted text-lg leading-relaxed mb-8 max-w-md">
            LocalMate je živá komunita služieb a tovaru. AI nájde najlepšieho poskytovateľa
            vo vašej štvrti za sekundy. Bez sprostredkovateľov, s platbou tokenmi.
          </motion.p>

          <motion.div {...fadeUp(0.3)} className="flex gap-3 flex-wrap">
            <Link to="/register" className="btn-primary text-base px-7 py-3">
              🎁 Registrovať sa (+50 tokenov)
            </Link>
            <Link to="/search" className="btn-ghost text-base px-7 py-3">
              Hľadať službu →
            </Link>
          </motion.div>

          <motion.div {...fadeUp(0.4)} className="flex gap-10 mt-12">
            {[['12K+', 'Členov'], ['340+', 'Kategórií'], ['98%', 'Spokojnosť']].map(([n, l]) => (
              <div key={l}>
                <div className="font-display font-bold text-3xl">{n}</div>
                <div className="text-xs text-muted mt-0.5">{l}</div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Map card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="card p-6"
        >
          <MapPreview />
        </motion.div>
      </section>

      {/* ── How it works ── */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-t border-border">
        <SectionLabel>Ako to funguje</SectionLabel>
        <h2 className="font-display font-black text-4xl tracking-tight mb-12">
          Jednoducho a prehľadne
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { n: '01', icon: '📍', t: 'Registruj sa', d: 'Uveď lokalitu a čo ponúkaš. Dostaneš 50 tokenov.' },
            { n: '02', icon: '🤖', t: 'AI hľadá', d: 'Napíš dopyt. AI nájde najbližšieho vhodného človeka.' },
            { n: '03', icon: '🪙', t: 'Otvor kontakt', d: 'Míňaj tokeny na zobrazenie kontaktu (5 LM).' },
            { n: '04', icon: '🎮', t: 'Leveluj', d: 'Za každý gig +10 XP. Vyšší level = vyššia viditeľnosť.' },
          ].map((s, i) => (
            <motion.div
              key={s.n}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -4, borderColor: 'rgba(124,92,252,0.5)' }}
              className="card p-6 transition-colors duration-200 cursor-default"
            >
              <div className="font-display font-black text-5xl text-border mb-4 select-none">{s.n}</div>
              <div className="text-3xl mb-3">{s.icon}</div>
              <div className="font-bold text-base mb-2">{s.t}</div>
              <div className="text-sm text-muted leading-relaxed">{s.d}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Level system ── */}
      <section className="border-t border-b border-border" style={{ background: 'var(--surface)' }}>
        <div className="max-w-6xl mx-auto px-6 py-16">
          <SectionLabel>Systém úrovní</SectionLabel>
          <h2 className="font-display font-black text-4xl tracking-tight mb-4">
            Rastieš s každým gigom
          </h2>
          <p className="text-muted text-base mb-12 max-w-lg">
            Nie recenzie — skutočný progres ako v hre. Vyšší level = vyššia viditeľnosť v AI vyhľadávaní.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {LEVELS.map((lv, i) => (
              <motion.div
                key={lv.level}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                whileHover={{ y: -4 }}
                className="card p-5 text-center"
              >
                <LevelBadge level={lv.level} levelName={lv.name} />
                <div className="text-xs text-muted mt-3 mb-3">{lv.req}</div>
                <div className="flex flex-col gap-1.5">
                  {lv.perks.map(p => (
                    <div key={p} className="text-xs bg-surface rounded-lg px-2 py-1.5">{p}</div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Token economy ── */}
      <section className="max-w-6xl mx-auto px-6 py-16 border-b border-border">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <div>
            <SectionLabel>Tokenová ekonomika</SectionLabel>
            <h2 className="font-display font-black text-4xl tracking-tight mb-4">
              Tokeny — mena komunity
            </h2>
            <p className="text-muted text-base mb-8 leading-relaxed">
              Všetko funguje na tokenoch. Dostaneš ich pri registrácii, zarobiš za gig, môžeš dokúpiť.
              Výber peňazí — len pre živnostníkov (IČO).
            </p>
            <Link to="/register" className="btn-primary text-base px-7 py-3 inline-block">
              Získať 50 tokenov zadarmo
            </Link>
          </div>
          <div className="flex flex-col gap-3">
            {[
              { icon: '🎁', t: 'Uvítací bonus', d: 'Pri registrácii', a: '+50 LM', c: 'text-accent2' },
              { icon: '👁', t: 'Otvoriť kontakt', d: 'Jednorazová platba', a: '−5 LM', c: 'text-accent' },
              { icon: '✅', t: 'Platba za gig', d: 'Priamo poskytovateľovi', a: '−? LM', c: 'text-accent' },
              { icon: '💳', t: 'Kúpiť tokeny', d: 'Dobíjanie zostatku', a: 'od 2.99€', c: 'text-gold' },
              { icon: '🏦', t: 'Výber → €', d: 'Vyžaduje IČO / živnosť', a: 'Len IČO', c: 'text-red-400' },
            ].map((r, i) => (
              <motion.div
                key={r.t}
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.07 }}
                className="card px-4 py-3.5 flex items-center gap-4"
              >
                <span className="text-2xl">{r.icon}</span>
                <div className="flex-1">
                  <div className="font-semibold text-sm">{r.t}</div>
                  <div className="text-xs text-muted">{r.d}</div>
                </div>
                <span className={`font-display font-bold text-sm ${r.c}`}>{r.a}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="font-display font-black text-5xl tracking-tight mb-6"
        >
          Začni dnes.<br />
          <span className="text-accent">Zadarmo.</span>
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="text-muted text-lg mb-10"
        >
          50 tokenov na uvítanie. Žiadna kreditná karta.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
        >
          <Link to="/register" className="btn-green text-lg px-10 py-4 inline-block rounded-2xl">
            🎁 Registrovať sa zadarmo
          </Link>
        </motion.div>
      </section>
    </div>
  )
}

// ─── Fake map preview ─────────────────────────────────────────────────────────
function MapPreview() {
  return (
    <div>
      <div className="relative rounded-2xl overflow-hidden mb-3"
           style={{ height: 280, background: 'var(--surface)' }}>
        {/* Grid */}
        <div className="absolute inset-0" style={{
          backgroundImage: 'linear-gradient(rgba(124,92,252,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(124,92,252,0.07) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }} />
        {/* Roads */}
        <div className="absolute inset-0" style={{
          background: 'linear-gradient(35deg, transparent 40%, rgba(124,92,252,0.13) 40.5%, transparent 41%), linear-gradient(120deg, transparent 30%, rgba(0,229,160,0.08) 30.5%, transparent 31%)',
        }} />
        {/* Search bar */}
        <div className="absolute top-3 left-3 right-3 rounded-xl px-4 py-2.5 flex items-center gap-2
                        text-sm text-muted border border-border backdrop-blur-sm"
             style={{ background: 'rgba(22,22,31,0.9)' }}>
          🔍 Hľadám: oprava iPhone v okolí...
        </div>
        {/* Pins */}
        {[
          { top: '28%', left: '20%', label: '💇 Kaderník', cls: 'text-accent border-accent/40' },
          { top: '55%', left: '72%', label: '🔧 Inštalatér', cls: 'text-accent2 border-accent2/40' },
          { top: '33%', left: '63%', label: '📱 Oprava tel.', cls: 'text-accent border-accent/40' },
          { top: '68%', left: '28%', label: '🎸 Gitara', cls: 'text-gold border-gold/40' },
        ].map((pin) => (
          <motion.div
            key={pin.label}
            whileHover={{ scale: 1.12 }}
            className="absolute flex flex-col items-center cursor-pointer z-10"
            style={{ top: pin.top, left: pin.left }}
          >
            <div className={`text-xs font-bold px-2.5 py-1 rounded-lg border mb-1 backdrop-blur-sm ${pin.cls}`}
                 style={{ background: 'rgba(22,22,31,0.9)' }}>
              {pin.label}
            </div>
            <div className="w-2.5 h-2.5 rounded-full border-2 border-white bg-current" />
          </motion.div>
        ))}
        {/* You */}
        <div className="absolute" style={{ top: '50%', left: '50%', transform: 'translate(-50%,-50%)' }}>
          <motion.div
            animate={{ boxShadow: ['0 0 0 0 rgba(0,229,160,0.4)', '0 0 0 20px rgba(0,229,160,0)', '0 0 0 0 rgba(0,229,160,0)'] }}
            transition={{ repeat: Infinity, duration: 2.5 }}
            className="w-14 h-14 rounded-full flex items-center justify-center border border-accent2/30"
            style={{ background: 'rgba(0,229,160,0.1)' }}
          >
            <div className="w-4 h-4 rounded-full bg-accent2 border-2 border-white" />
          </motion.div>
        </div>
      </div>
      {/* Results */}
      {[
        { emoji: '🔧', name: 'Artúr K.', sub: 'Oprava smartfónov', dist: '0.4 km', level: 4 },
        { emoji: '📱', name: 'Servis Fix', sub: 'Elektronika', dist: '1.2 km', level: 2 },
      ].map((r, i) => (
        <motion.div
          key={r.name}
          whileHover={{ borderColor: 'rgba(124,92,252,0.5)' }}
          className="flex items-center gap-3 border border-border rounded-xl px-4 py-3 mb-2
                     transition-colors duration-200 cursor-pointer"
          style={{ background: 'var(--surface)', opacity: i === 1 ? 0.6 : 1 }}
        >
          <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0"
               style={{ background: 'linear-gradient(135deg,#7c5cfc,#c084fc)' }}>
            {r.emoji}
          </div>
          <div className="flex-1">
            <div className="font-bold text-sm">{r.name}</div>
            <div className="text-xs text-muted flex items-center gap-2">
              {r.sub}
              <LevelBadge level={r.level} levelName="" small />
            </div>
          </div>
          <div className="text-xs font-bold text-accent2 bg-accent2/10 px-2.5 py-1 rounded-full">
            {r.dist}
          </div>
        </motion.div>
      ))}
    </div>
  )
}
