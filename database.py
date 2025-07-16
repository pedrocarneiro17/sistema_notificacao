# database.py
import sqlite3
import datetime # Make sure datetime is imported here for delete_licenca_passada

DATABASE_NAME = "datas_importantes.db"

def connect_db():
    """Conecta ao banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Retorna linhas como dicionários (acesso por nome da coluna)
    return conn

def create_table():
    """Cria a tabela 'funcionarios' se ela não existir."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_admissao TEXT NOT NULL,      -- Armazenará DD/MM/AAAA
            data_aniversario TEXT NOT NULL,   -- Armazenará DD/MM/AAAA
            data_retorno_licenca TEXT         -- Armazenará DD/MM/AAAA ou NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_funcionario(nome, data_admissao, data_aniversario, data_retorno_licenca=None):
    """Insere um novo funcionário no banco de dados."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO funcionarios (nome, data_admissao, data_aniversario, data_retorno_licenca)
        VALUES (?, ?, ?, ?)
    ''', (nome, data_admissao, data_aniversario, data_retorno_licenca))
    conn.commit()
    conn.close()

def get_all_funcionarios():
    """Retorna todos os funcionários registrados."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM funcionarios ORDER BY nome ASC")
    funcionarios = cursor.fetchall()
    conn.close()
    return funcionarios

def get_funcionario_by_id(funcionario_id):
    """Retorna um funcionário pelo ID."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM funcionarios WHERE id = ?", (funcionario_id,))
    funcionario = cursor.fetchone()
    conn.close()
    return funcionario

def update_funcionario(funcionario_id, nome, data_admissao, data_aniversario, data_retorno_licenca=None):
    """Atualiza os dados de um funcionário."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE funcionarios
        SET nome = ?, data_admissao = ?, data_aniversario = ?, data_retorno_licenca = ?
        WHERE id = ?
    ''', (nome, data_admissao, data_aniversario, data_retorno_licenca, funcionario_id))
    conn.commit()
    conn.close()

def delete_funcionario(funcionario_id):
    """Deleta um funcionário do banco de dados pelo ID."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM funcionarios WHERE id = ?", (funcionario_id,))
    conn.commit()
    conn.close()

def delete_licenca_passada():
    """Define a data_retorno_licenca como NULL para licenças que já passaram."""
    conn = connect_db()
    cursor = conn.cursor()
    hoje_str = datetime.datetime.now().strftime('%d/%m/%Y')
    cursor.execute('''
        UPDATE funcionarios
        SET data_retorno_licenca = NULL
        WHERE data_retorno_licenca IS NOT NULL
        AND SUBSTR(data_retorno_licenca, 7, 4) || SUBSTR(data_retorno_licenca, 4, 2) || SUBSTR(data_retorno_licenca, 1, 2) <= SUBSTR(?, 7, 4) || SUBSTR(?, 4, 2) || SUBSTR(?, 1, 2)
    ''', (hoje_str, hoje_str, hoje_str))
    conn.commit()
    conn.close()
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificação de licenças passadas executada.")

# Inicializa o banco de dados e cria a tabela ao importar
create_table()