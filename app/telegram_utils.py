import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

async def processar_mensagem_telegram(payload: dict):
    try:
        mensagem = payload.get("message", {})
        texto = mensagem.get("text")
        chat_id = mensagem.get("chat", {}).get("id")

        if not texto or not chat_id:
            return

        # Exemplo simples de resposta fixa
        resposta = f"Oi, aqui é a Dra. Ana 👩‍⚕️. Me conta seu nome e idade pra eu te ajudar direitinho 💗"

        await enviar_mensagem(chat_id, resposta)

    except Exception as e:
        print(f"Erro ao processar mensagem do Telegram: {e}")

async def enviar_mensagem(chat_id: int, texto: str):
    async with httpx.AsyncClient() as client:
        await client.post(API_URL, json={
            "chat_id": chat_id,
            "text": texto
        })
