from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

config = ConnectionConfig(
  MAIL_USERNAME="dov@luxemporiumusa.com",
  MAIL_PASSWORD="ftit mdgn hkmy lysv",
  MAIL_FROM="dov@luxemporiumusa.com",
  MAIL_FROM_NAME="PO Tool Errors",
  MAIL_PORT=587,
  MAIL_SERVER="smtp.gmail.com",
  MAIL_STARTTLS=True,
  MAIL_SSL_TLS=False,
)

async def send_error_email(subject: str, error_message: str):
  message = MessageSchema(
    subject=subject,
    recipients=["dov@luxemporiumusa.com"],
    body=f"{subject}:\n\n{error_message}",
    subtype=MessageType("plain"),
  )

  fm = FastMail(config=config)

  await fm.send_message(message=message)
  print("Sent error email.")