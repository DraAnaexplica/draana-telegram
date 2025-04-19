import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import requests
from sqlalchemy import create_engine, Column, Integer, String, Text
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
        logger.error(f"Erro ao chamar OpenRouter: {e}")
        return "Desculpe, houve um erro ao processar sua solicitação."

# Função para salvar mensagem no banco
def save_message(user_id: int, message: str, response: str):
    session = Session()
    try:
        user_message = UserMessage(user_id=user_id, message=message, response=response)
        session.add(user_message)
        session.commit()
    except Exception as e:
        logger.error(f"Erro ao salvar mensagem: {e}")
        session.rollback()
    finally:
        session.close()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Sou seu chatbot. Envie uma mensagem e responderei usando IA!"
    )

# Manipulador de mensagens
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id

    # Chama o OpenRouter para obter resposta
    response = await call_openrouter(user_message)

    # Salva a interação no banco
    save_message(user_id, user_message, response)

    # Responde ao usuário
    await update.message.reply_text(response)

# Manipulador de erros
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")
    if update and update.message:
        await update.message.reply_text("Ocorreu um erro. Tente novamente.")

# Função principal
def main():
    if not all([TELEGRAM_TOKEN, OPENROUTER_API_KEY, DATABASE_URL]):
        logger.error("Variáveis de ambiente não configuradas corretamente.")
        return

    # Inicializa o bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Inicia o bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()