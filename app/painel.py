import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

DATABASE_URL = os.getenv("DATABASE_URL")

# --- Funções auxiliares ---
def conectar():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# --- TABELAS ---
def criar_tabela_tokens():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL UNIQUE,
                token TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validade TIMESTAMP NOT NULL
            )
        ''')
        conn.commit()

def criar_tabela_chat_history():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# --- TOKENS ---
def inserir_token(nome, telefone, dias_validade):
    import secrets
    token = secrets.token_hex(16)
    validade = datetime.utcnow() + timedelta(days=dias_validade)
    try:
        with conectar() as conn, conn.cursor() as cur:
            cur.execute('''
                INSERT INTO tokens (nome, telefone, token, validade)
                VALUES (%s, %s, %s, %s)
                RETURNING token
            ''', (nome, telefone, token, validade))
            conn.commit()
            return cur.fetchone()['token']
    except psycopg2.errors.UniqueViolation:
        return None

def listar_tokens():
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('SELECT * FROM tokens ORDER BY id DESC')
        return cur.fetchall()

def excluir_token(token):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('DELETE FROM tokens WHERE token = %s', (token,))
        conn.commit()
        return cur.rowcount > 0

def verificar_token_valido(token):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            SELECT * FROM tokens
            WHERE token = %s AND validade >= CURRENT_TIMESTAMP
        ''', (token,))
        return cur.fetchone() is not None

def atualizar_validade_token(token_a_atualizar, dias_a_adicionar):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            UPDATE tokens SET validade = validade + interval '%s day'
            WHERE token = %s
        ''', (dias_a_adicionar, token_a_atualizar))
        conn.commit()
        return cur.rowcount > 0

def buscar_token_ativo_por_telefone(telefone_a_buscar):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            SELECT token FROM tokens
            WHERE telefone = %s AND validade >= CURRENT_TIMESTAMP
        ''', (telefone_a_buscar,))
        row = cur.fetchone()
        return row['token'] if row else None

# --- CHAT MEMORY ---
def add_chat_message(user_token, role, content):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            INSERT INTO chat_history (user_id, role, content)
            VALUES (%s, %s, %s)
        ''', (user_token, role, content))
        conn.commit()

def get_chat_history(user_token, limit=20):
    with conectar() as conn, conn.cursor() as cur:
        cur.execute('''
            SELECT role, content FROM chat_history
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (user_token, limit))
        rows = cur.fetchall()
        return list(reversed([{"role": row['role'], "content": row['content']} for row in rows]))
