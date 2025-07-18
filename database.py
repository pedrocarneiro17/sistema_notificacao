# database.py
import sqlite3
import datetime
import os

DATABASE = os.path.join("/mnt/data/", "datas_importantes.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_admissao TEXT NOT NULL,
            data_aniversario TEXT NOT NULL,
            data_retorno_licenca TEXT
        )
    ''')
    # NOVO: Tabela para clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_aniversario TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_funcionario(nome, data_admissao, data_aniversario, data_retorno_licenca):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO funcionarios (nome, data_admissao, data_aniversario, data_retorno_licenca)
        VALUES (?, ?, ?, ?)
    ''', (nome, data_admissao, data_aniversario, data_retorno_licenca))
    conn.commit()
    conn.close()

# NOVO: Funções para clientes
def insert_cliente(nome, data_aniversario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clientes (nome, data_aniversario)
        VALUES (?, ?)
    ''', (nome, data_aniversario))
    conn.commit()
    conn.close()

def get_all_funcionarios():
    conn = get_db_connection()
    funcionarios = conn.execute('SELECT * FROM funcionarios ORDER BY nome').fetchall()
    conn.close()
    return funcionarios

# NOVO: Função para obter todos os clientes
def get_all_clientes():
    conn = get_db_connection()
    clientes = conn.execute('SELECT * FROM clientes ORDER BY nome').fetchall()
    conn.close()
    return clientes

def get_funcionario_by_id(funcionario_id):
    conn = get_db_connection()
    funcionario = conn.execute('SELECT * FROM funcionarios WHERE id = ?', (funcionario_id,)).fetchone()
    conn.close()
    return funcionario

# NOVO: Função para obter cliente por ID (se for necessário editar/deletar um dia)
def get_cliente_by_id(cliente_id):
    conn = get_db_connection()
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    conn.close()
    return cliente

def update_funcionario(funcionario_id, nome, data_admissao, data_aniversario, data_retorno_licenca):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE funcionarios
        SET nome = ?, data_admissao = ?, data_aniversario = ?, data_retorno_licenca = ?
        WHERE id = ?
    ''', (nome, data_admissao, data_aniversario, data_retorno_licenca, funcionario_id))
    conn.commit()
    conn.close()

# NOVO: Função para atualizar cliente (se for necessário editar um dia)
def update_cliente(cliente_id, nome, data_aniversario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE clientes
        SET nome = ?, data_aniversario = ?
        WHERE id = ?
    ''', (nome, data_aniversario, cliente_id))
    conn.commit()
    conn.close()

def delete_funcionario(funcionario_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM funcionarios WHERE id = ?', (funcionario_id,))
    conn.commit()
    conn.close()

# NOVO: Função para deletar cliente (se for necessário deletar um dia)
def delete_cliente(cliente_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()


def delete_licenca_passada():
    conn = get_db_connection()
    cursor = conn.cursor()
    hoje = datetime.date.today().strftime('%d/%m/%Y')
    # Atualiza para NULL se a data de retorno de licença for passada
    cursor.execute('''
        UPDATE funcionarios
        SET data_retorno_licenca = NULL
        WHERE data_retorno_licenca IS NOT NULL AND
              SUBSTR(data_retorno_licenca, 7, 4) || SUBSTR(data_retorno_licenca, 4, 2) || SUBSTR(data_retorno_licenca, 1, 2) <
              SUBSTR(?, 7, 4) || SUBSTR(?, 4, 2) || SUBSTR(?, 1, 2)
    ''', (hoje, hoje, hoje))
    conn.commit()
    conn.close()