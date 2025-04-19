import os
import httpx

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "deepseek/deepseek-chat-v3-0324"

def carregar_prompt():
    with open("app/prompt/system_prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

def gerar_resposta_openrouter(mensagem_usuario: str) -> str:
    prompt_sistema = carregar_prompt()

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensagem_usuario}
        ],
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = httpx.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        resposta = response.json()["choices"][0]["message"]["content"]
        return resposta
    except Exception as e:
        print(f"Erro ao gerar resposta via OpenRouter: {e}")
        return "Desculpe, algo deu errado ao tentar responder agora."
