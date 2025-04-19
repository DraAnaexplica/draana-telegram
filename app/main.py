import os
import logging
import requests
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações do ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Ex.: https://your-render-app.onrender.com/webhook

# Verifica variáveis de ambiente
if not all([TELEGRAM_TOKEN, OPENROUTER_API_KEY, DATABASE_URL, WEBHOOK_URL]):
    logger.error("Missing environment variables.")
    raise ValueError("Please set TELEGRAM_TOKEN, OPENROUTER_API_KEY, DATABASE_URL, and WEBHOOK_URL")

# Configuração do banco de dados
Base = declarative_base()

class UserMessage(Base):
    __tablename__ = "user_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Inicializa FastAPI
app = FastAPI()

# Inicializa o bot do Telegram
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# Função para chamar o OpenRouter
async def call_openrouter(message: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [{"role": "user", "content": message}],
    }
    try:
        response = requests.post(OPENROUTER_URL, json=data, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as e:
        logger.error(f"Error calling OpenRouter: {e}")
        return "Sorry, there was an error processing your request."

# Função para salvar mensagem no banco
def save_message(user_id: int, message: str, response: str):
    session = Session()
    try:
        user_message = UserMessage(user_id=user_id, message=message, response=response)
        session.add(user_message)
        session.commit()
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        session.rollback()
    finally:
        session.close()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm your chatbot. Send a message, and I'll respond using AI!"
    )

# Manipulador de mensagens
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id

    # Chama o OpenRouter
    response = await call_openrouter(user_message)

    # Salva no banco
    save_message(user_id, user_message, response)

    # Responde ao usuário
    await update.message.reply_text(response)

# Manipulador de erros
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("An error occurred. Please try again.")

# Configura os handlers do Telegram
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_error_handler(error_handler)

# Endpoint para webhook do Telegram
@app.post("/webhook")
async def webhook(request: Request):
    update = await request.json()
    await telegram_app.update_queue.put(Update.de_json(update, telegram_app.bot))
    return {"status": "ok"}

# Inicializa o webhook
@app.on_event("startup")
async def startup():
    await telegram_app.bot.set_webhook(url=WEBHOOK_URL)
    await telegram_app.start()
    logger.info("Webhook set and application started")

@app.on_event("shutdown")
async def shutdown():
    await telegram_app.stop()
    logger.info("Application stopped")

# Endpoint de saúde
@app.get("/")
async def health():
    return {"status": "running"}