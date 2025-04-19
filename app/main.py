from fastapi import FastAPI, Request
import httpx
import os
from app.openrouter_utils import gerar_resposta_openrouter
from app.telegram_utils import enviar_mensagem_telegram
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

@app.post("/webhook")
async def receber_mensagem(request: Request):
    payload = await request.json()
    try:
        message = payload["message"]
        user_id = message["from"]["id"]
        nome_usuario = message["from"].get("first_name", "")
        texto = message.get("text", "")

        print(f"📩 Mensagem recebida de {nome_usuario}: {texto}")

        resposta = gerar_resposta_openrouter(texto)

        await enviar_mensagem_telegram(user_id, resposta)

        return {"status": "mensagem processada"}
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        return {"status": "erro", "detalhe": str(e)}
