from fastapi import FastAPI, Request
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
CHAVE_SECRETA = os.getenv("TABELA_SECRET", "proteger")

@app.get("/")
def raiz():
    return {"mensagem": "API da Dra. Ana - Telegram"}

@app.get("/criar-tabela")
def criar_tabela(request: Request):
    chave = request.query_params.get("chave")
    if chave != CHAVE_SECRETA:
        return {"erro": "Acesso negado. Chave inválida."}

    sql = """
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
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "✅ Tabela 'chat_history' criada com sucesso no Render"}
    except Exception as e:
        return {"erro": str(e)}
