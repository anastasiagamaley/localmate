"""
Email templates using Jinja2.
All emails share the same base layout with LocalMate branding.
"""
from jinja2 import Template

# ─── Base layout ──────────────────────────────────────────────────────────────

BASE = """
<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ subject }}</title>
  <style>
    body { margin: 0; padding: 0; background: #0a0a0f; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .wrapper { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
    .header { text-align: center; margin-bottom: 32px; }
    .logo { font-size: 28px; font-weight: 900; color: #f0f0f8; letter-spacing: -1px; }
    .logo span { color: #7c5cfc; }
    .card { background: #16161f; border: 1px solid #22222e; border-radius: 16px; padding: 32px; margin-bottom: 24px; }
    .title { font-size: 24px; font-weight: 800; color: #f0f0f8; margin: 0 0 8px 0; }
    .subtitle { font-size: 15px; color: #7a7a9a; margin: 0 0 24px 0; line-height: 1.6; }
    .token-box { background: rgba(245,200,66,0.08); border: 1px solid rgba(245,200,66,0.2); border-radius: 12px; padding: 16px 20px; margin: 20px 0; text-align: center; }
    .token-amount { font-size: 36px; font-weight: 900; color: #f5c842; }
    .token-label { font-size: 13px; color: #7a7a9a; margin-top: 4px; }
    .info-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #22222e; font-size: 14px; }
    .info-label { color: #7a7a9a; }
    .info-value { color: #f0f0f8; font-weight: 600; }
    .btn { display: inline-block; background: #7c5cfc; color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: 700; font-size: 15px; margin: 20px 0; }
    .btn-green { background: #00e5a0; color: #0a0a0f !important; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    .status-pending  { background: rgba(245,200,66,0.1);  color: #f5c842; }
    .status-accepted { background: rgba(124,92,252,0.1);  color: #7c5cfc; }
    .status-completed{ background: rgba(0,229,160,0.1);   color: #00e5a0; }
    .status-cancelled{ background: rgba(122,122,154,0.1); color: #7a7a9a; }
    .warning-box { background: rgba(255,107,107,0.08); border: 1px solid rgba(255,107,107,0.2); border-radius: 12px; padding: 14px 18px; margin: 16px 0; color: #ff6b6b; font-size: 14px; }
    .footer { text-align: center; color: #7a7a9a; font-size: 12px; margin-top: 32px; line-height: 1.8; }
    .divider { border: none; border-top: 1px solid #22222e; margin: 20px 0; }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="logo">Local<span>Mate</span></div>
    </div>
    {{ content }}
    <div class="footer">
      LocalMate · Lokálna komunita služieb<br>
      <a href="{{ app_url }}" style="color: #7c5cfc;">localmate.sk</a> ·
      Toto je automatická správa, neodpovedajte na ňu.
    </div>
  </div>
</body>
</html>
"""


def render(subject: str, content: str, app_url: str) -> str:
    return Template(BASE).render(subject=subject, content=content, app_url=app_url)


# ─── Email templates ──────────────────────────────────────────────────────────

def returning_user_email(name: str, app_url: str) -> tuple[str, str]:
    subject = "Vitaj späť v LocalMate! 👋"
    content = f"""
    <div class="card">
      <h1 class="title">Vitaj späť, {name or ''}! 👋</h1>
      <p class="subtitle">Tvoj účet bol obnovený. Môžeš pokračovať tam, kde si skončil.</p>
      <p style="color:#7a7a9a;font-size:14px;line-height:1.7;">
        Poznámka: Uvítací bonus tokenov sa udeľuje iba pri prvej registrácii.
      </p>
      <center><a href="{app_url}/search" class="btn">Pokračovať →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def welcome_email(name: str, tokens: int, app_url: str) -> tuple[str, str]:
    subject = "Vitaj v LocalMate! 🎉 Tvoje tokeny čakajú"
    content = f"""
    <div class="card">
      <h1 class="title">Vitaj, {name or 'nový člen'}! 🎉</h1>
      <p class="subtitle">Tvoj účet bol úspešne vytvorený. Si súčasťou lokálnej komunity LocalMate.</p>
      <div class="token-box">
        <div class="token-amount">🪙 {tokens} LM</div>
        <div class="token-label">Uvítací bonus — pridaný na tvoj účet</div>
      </div>
      <p style="color:#7a7a9a;font-size:14px;line-height:1.7;">
        Tokeny môžeš použiť na otvorenie kontaktov (5 LM) alebo platbu za služby.
        Začni tým, že si nastavíš profil a svoju lokalitu — potom ťa AI dokáže nájsť!
      </p>
      <center><a href="{app_url}/profile" class="btn">Nastaviť profil →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def verify_email(name: str, verify_url: str, app_url: str) -> tuple[str, str]:
    subject = "Potvrď svoj email — LocalMate"
    content = f"""
    <div class="card">
      <h1 class="title">Potvrď svoj email ✉️</h1>
      <p class="subtitle">Ahoj {name or ''}! Klikni na tlačidlo nižšie pre potvrdenie emailovej adresy.</p>
      <center><a href="{verify_url}" class="btn">Potvrdiť email</a></center>
      <hr class="divider">
      <p style="color:#7a7a9a;font-size:13px;">Link je platný 24 hodín. Ak si si nezaložil účet, ignoruj tento email.</p>
    </div>
    """
    return subject, render(subject, content, app_url)


def gig_created_provider(
    provider_name: str, client_name: str,
    gig_title: str, gig_price: int,
    gig_id: str, app_url: str
) -> tuple[str, str]:
    subject = f"Nový gig pre teba: {gig_title} 📋"
    content = f"""
    <div class="card">
      <h1 class="title">Máš nový gig! 📋</h1>
      <p class="subtitle">
        <strong style="color:#f0f0f8">{client_name or 'Klient'}</strong>
        ti vytvoril gig a čaká na tvoje prijatie.
      </p>
      <div style="margin: 20px 0;">
        <div class="info-row"><span class="info-label">Názov</span><span class="info-value">{gig_title}</span></div>
        <div class="info-row"><span class="info-label">Odmena</span><span class="info-value" style="color:#f5c842">🪙 {gig_price} LM</span></div>
        <div class="info-row"><span class="info-label">Stav</span><span class="status-badge status-pending">Čaká na prijatie</span></div>
      </div>
      <center><a href="{app_url}/gigs" class="btn">Prijať gig →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def gig_completed_provider(
    provider_name: str, gig_title: str,
    tokens_earned: int, new_level: str, app_url: str
) -> tuple[str, str]:
    subject = f"Gig dokončený! +{tokens_earned} LM na tvojom účte 🎉"
    content = f"""
    <div class="card">
      <h1 class="title">Gig dokončený! 🎉</h1>
      <p class="subtitle">Klient potvrdil dokončenie <strong style="color:#f0f0f8">{gig_title}</strong>. Tokeny boli prevedené.</p>
      <div class="token-box">
        <div class="token-amount">+{tokens_earned} LM</div>
        <div class="token-label">Prevedené na tvoj účet</div>
      </div>
      <div style="margin: 16px 0;">
        <div class="info-row"><span class="info-label">Tvoj level</span><span class="info-value" style="color:#7c5cfc">{new_level}</span></div>
      </div>
      <center><a href="{app_url}/tokens" class="btn btn-green">Zobraziť zostatok →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def gig_completed_client(
    client_name: str, gig_title: str,
    tokens_spent: int, app_url: str
) -> tuple[str, str]:
    subject = f"Platba potvrdená — {gig_title}"
    content = f"""
    <div class="card">
      <h1 class="title">Platba potvrdená ✅</h1>
      <p class="subtitle">Úspešne si dokončil gig <strong style="color:#f0f0f8">{gig_title}</strong>.</p>
      <div style="margin: 20px 0;">
        <div class="info-row"><span class="info-label">Zaplatené</span><span class="info-value" style="color:#f5c842">🪙 {tokens_spent} LM</span></div>
        <div class="info-row"><span class="info-label">Stav</span><span class="status-badge status-completed">Dokončený</span></div>
      </div>
      <center><a href="{app_url}/gigs" class="btn">Zobraziť moje gigy</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def gig_cancelled(
    recipient_name: str, gig_title: str,
    cancelled_by: str, reason: str, app_url: str
) -> tuple[str, str]:
    subject = f"Gig zrušený — {gig_title}"
    content = f"""
    <div class="card">
      <h1 class="title">Gig bol zrušený ❌</h1>
      <p class="subtitle">Gig <strong style="color:#f0f0f8">{gig_title}</strong> bol zrušený.</p>
      <div style="margin: 20px 0;">
        <div class="info-row"><span class="info-label">Zrušil</span><span class="info-value">{cancelled_by}</span></div>
        {'<div class="warning-box">Dôvod: ' + reason + '</div>' if reason else ''}
      </div>
      <center><a href="{app_url}/gigs" class="btn">Zobraziť moje gigy</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def contact_opened_provider(
    provider_name: str, app_url: str
) -> tuple[str, str]:
    subject = "Niekto si pozrel tvoj kontakt 👁"
    content = f"""
    <div class="card">
      <h1 class="title">Záujem o tvoje služby! 👁</h1>
      <p class="subtitle">Niekto si otvoril tvoj kontakt cez LocalMate. Možno čoskoro dostaneš ponuku na gig!</p>
      <p style="color:#7a7a9a;font-size:14px;line-height:1.7;">
        Uisti sa že máš aktuálny profil a popis svojich služieb — to zvyšuje šancu na úspech.
      </p>
      <center><a href="{app_url}/profile" class="btn">Upraviť profil →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def low_tokens_warning(
    name: str, balance: int, app_url: str
) -> tuple[str, str]:
    subject = f"Tvoje tokeny dochádzajú — zostatok: {balance} LM 🪙"
    content = f"""
    <div class="card">
      <h1 class="title">Tokeny dochádzajú ⚠️</h1>
      <p class="subtitle">Ahoj {name or ''}! Tvoj zostatok tokenov je nízky.</p>
      <div class="token-box">
        <div class="token-amount" style="color:#ff6b6b">🪙 {balance} LM</div>
        <div class="token-label">Aktuálny zostatok</div>
      </div>
      <p style="color:#7a7a9a;font-size:14px;line-height:1.7;">
        Na otvorenie kontaktu potrebuješ 5 LM. Doplň si tokeny a pokračuj v hľadaní!
      </p>
      <center><a href="{app_url}/tokens" class="btn">Kúpiť tokeny →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)


def level_up_email(
    name: str, new_level: str, gigs_count: int, app_url: str
) -> tuple[str, str]:
    subject = f"Gratulujeme! Dosiahol si nový level: {new_level} 🎮"
    content = f"""
    <div class="card">
      <h1 class="title">Level nahor! 🎮</h1>
      <p class="subtitle">Gratulujeme, {name or ''}! Tvoja tvrdá práca sa vypláca.</p>
      <div class="token-box" style="background:rgba(124,92,252,0.08);border-color:rgba(124,92,252,0.2);">
        <div class="token-amount" style="color:#7c5cfc">{new_level}</div>
        <div class="token-label">{gigs_count} dokončených gigov</div>
      </div>
      <p style="color:#7a7a9a;font-size:14px;line-height:1.7;">
        Vyšší level znamená väčšiu viditeľnosť v AI vyhľadávaní. Pokračuj v skvelej práci!
      </p>
      <center><a href="{app_url}/profile" class="btn">Zobraziť profil →</a></center>
    </div>
    """
    return subject, render(subject, content, app_url)
