"""
Email sender using Resend.
In development (no API key) — logs emails to console instead of sending.
"""
import logging

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, api_key: str, from_email: str, from_name: str, environment: str):
        self.from_email = from_email
        self.from_name = from_name
        self.from_address = f"{from_name} <{from_email}>"
        self.environment = environment
        self._ready = False

        if api_key:
            try:
                import resend
                resend.api_key = api_key
                self._ready = True
                logger.info("Resend email sender ready ✅")
            except Exception as e:
                logger.warning(f"Resend init failed: {e}")
        else:
            logger.warning("No RESEND_API_KEY — emails logged only (dev mode)")

    async def send(self, to_email: str, subject: str, html_content: str) -> bool:
        if not self._ready:
            logger.info(
                f"\n{'='*60}\n"
                f"📧 EMAIL (dev mode — not sent)\n"
                f"To: {to_email}\n"
                f"Subject: {subject}\n"
                f"{'='*60}"
            )
            return True

        try:
            import resend
            email = resend.Emails.send({
                "from": self.from_address,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            })
            logger.info(f"Email sent to {to_email}: {subject} | id={email.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Email send failed to {to_email}: {e}")
            return False
