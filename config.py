import os
import psycopg2
import psycopg2.extras

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_NAME     = os.getenv("DB_NAME",     "db_atendimento_webservice")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "M@qu1n@V1rtu@L")

SECRET_KEY  = os.getenv("FLASK_SECRET_KEY", "entrega4_rest_2026")

# Enderecos dos outros sistemas via VPN.
ESTOQUE_BASE_URL    = os.getenv("ESTOQUE_URL",    "http://localhost:5003")
FINANCEIRO_BASE_URL = os.getenv("FINANCEIRO_URL", "http://localhost:5004")

# Tempo maximo de espera por resposta REST em segundos.
# Se o outro sistema nao responder nesse prazo, a chamada falha.
REST_TIMEOUT = int(os.getenv("REST_TIMEOUT", "10"))


def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,      # <-- Verifique se tem essa vírgula aqui!
        password=DB_PASSWORD, 
        client_encoding='utf8'
    )


def get_cur(db):
    # DictCursor permite acessar colunas pelo nome: row["cpf"]
    return db.cursor(cursor_factory=psycopg2.extras.DictCursor)
