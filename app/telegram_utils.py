import os
import requests
import json
from dotenv import load_dotenv
from app.openrouter_utils import gerar_resposta_openrouter
from app.painel import add_chat_message, get_chat_history

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN não configurado.")

SYSTEM_PROMPT = "Assistente."
SYSTEM_PROMPT_FILE = "system_prompt.txt"
if os.path.exists(SYSTEM_PROMPT_FILE):
    with open(SYSTEM_PROMPT_FILE, encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()

# Função principal chamada pelo webhook
async def processar_mensagem_telegram(payload: dict) -> dict:
    try:
        mensagem = payload.get("message", {})
        user_info = mensagem.get("from", {})
        texto = mensagem.get("text", "").strip()

        user_id = str(user_info.get("id"))
        nome_usuario = user_info.get("first_name", "amiga")

        if not texto:
            return {"erro": "Mensagem vazia ou não suportada."}

        # Salva a mensagem do usuário
        add_chat_message(user_id, "user", texto)

        # Recupera até 20 mensagens anteriores
        historico = get_chat_history(user_id, limit=20)
        mensagens_para_ia = [{"role": "system", "content": SYSTEM_PROMPT}] + historico

        # Gera resposta com IA
        resposta_ia = gerar_resposta_openrouter(mensagens_para_ia)

        # Salva resposta da IA
        add_chat_message(user_id, "assistant", resposta_ia)

        # Envia resposta de volta para o Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload_envio = {
            "chat_id": user_id,
            "text": resposta_ia
        }
        requests.post(url, json=payload_envio)

        return {
            "user_id": user_id,
            "nome": nome_usuario,
            "mensagem": texto,
            "resposta": resposta_ia
        }

    except Exception as e:
        return {"erro": f"Erro ao processar mensagem: {str(e)}"}
