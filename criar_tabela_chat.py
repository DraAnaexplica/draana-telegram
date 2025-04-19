import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("🔎 DATABASE_URL =", DATABASE_URL)

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
    print("✅ Tabela 'chat_history' criada com sucesso!")
except Exception as e:
    print(f"❌ Erro ao criar tabela: {e}")
