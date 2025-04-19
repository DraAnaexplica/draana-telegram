import httpx
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

async def enviar_mensagem_telegram(chat_id: int, texto: str):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            print("✅ Mensagem enviada com sucesso.")
        except Exception as e:
            print(f"Erro ao enviar mensagem para Telegram: {e}")
