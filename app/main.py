from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import psycopg2
from app.telegram_utils import processar_mensagem_telegram

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/")
def home():
    return {"status": "ok", "mensagem": "API Dra. Ana Telegram ativa"}

@app.get("/criar-tabela")
def criar_tabela(chave: str):
    chave_correta = os.getenv("TABELA_SECRET")
    if chave != chave_correta:
        return JSONResponse(content={"erro": "Acesso negado. Chave inválida."}, status_code=401)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(create_table_sql)
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "✅ Tabela 'chat_history' criada com sucesso no Render"}
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/webhook")
async def receber_mensagem_telegram(request: Request):
    try:
        body = await request.json()
        await processar_mensagem_telegram(body)
        return {"status": "ok"}
    except Exception as e:
        return {"erro": str(e)}
