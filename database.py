# database.py
import sqlite3
import datetime
import os

# ATENÇÃO: Use o mesmo caminho do volume persistente que seu app.py usa!
DATABASE_NAME = os.path.join("/mnt/data/", "datas_importantes.db")

def connect_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = connect_db()
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
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO funcionarios (nome, data_admissao, data_aniversario, data_retorno_licenca)
        VALUES (?, ?, ?, ?)
    ''', (nome, data_admissao, data_aniversario, data_retorno_licenca))
    conn.commit()
    conn.close()

def insert_cliente(nome, data_aniversario):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO clientes (nome, data_aniversario)
        VALUES (?, ?)
    ''', (nome, data_aniversario))
    conn.commit()
    conn.close()

def get_all_funcionarios():
    conn = connect_db()
    funcionarios = conn.execute('SELECT * FROM funcionarios ORDER BY nome').fetchall()
    conn.close()
    return funcionarios

def get_all_clientes():
    conn = connect_db()
    clientes = conn.execute('SELECT * FROM clientes ORDER BY nome').fetchall()
    conn.close()
    return clientes

def get_funcionario_by_id(funcionario_id):
    conn = connect_db()
    funcionario = conn.execute('SELECT * FROM funcionarios WHERE id = ?', (funcionario_id,)).fetchone()
    conn.close()
    return funcionario

def get_cliente_by_id(cliente_id):
    conn = connect_db()
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,)).fetchone()
    conn.close()
    return cliente

def update_funcionario(funcionario_id, nome, data_admissao, data_aniversario, data_retorno_licenca):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE funcionarios
        SET nome = ?, data_admissao = ?, data_aniversario = ?, data_retorno_licenca = ?
        WHERE id = ?
    ''', (nome, data_admissao, data_aniversario, data_retorno_licenca, funcionario_id))
    conn.commit()
    conn.close()

def update_cliente(cliente_id, nome, data_aniversario):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE clientes
        SET nome = ?, data_aniversario = ?
        WHERE id = ?
    ''', (nome, data_aniversario, cliente_id))
    conn.commit()
    conn.close()

def delete_funcionario(funcionario_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM funcionarios WHERE id = ?', (funcionario_id,))
    conn.commit()
    conn.close()

def delete_cliente(cliente_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()

def delete_licenca_passada():
    conn = connect_db()
    cursor = conn.cursor()
    hoje = datetime.date.today().strftime('%d/%m/%Y')
    cursor.execute('''
        UPDATE funcionarios
        SET data_retorno_licenca = NULL
        WHERE data_retorno_licenca IS NOT NULL AND
              SUBSTR(data_retorno_licenca, 7, 4) || SUBSTR(data_retorno_licenca, 4, 2) || SUBSTR(data_retorno_licenca, 1, 2) <
              SUBSTR(?, 7, 4) || SUBSTR(?, 4, 2) || SUBSTR(?, 1, 2)
    ''', (hoje, hoje, hoje))
    conn.commit()
    conn.close()