# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import insert_funcionario, get_all_funcionarios, create_table, get_funcionario_by_id, update_funcionario, delete_funcionario, delete_licenca_passada
import datetime
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Certifica que a tabela é criada ao iniciar o Flask
create_table()

# Agendamento para verificar e excluir licenças passadas diariamente
# Roda à meia-noite (00:00)
@scheduler.task('cron', id='delete_old_licenses', hour=0, minute=0)
def job_delete_licenca_passada():
    with app.app_context(): # Necessário para rodar fora do contexto de requisição
        delete_licenca_passada()

@app.route('/')
def index():
    """Rota principal que exibe o formulário e a lista de funcionários."""
    funcionarios = get_all_funcionarios()
    return render_template('index.html', funcionarios=funcionarios)

@app.route('/adicionar_funcionario', methods=['POST'])
def adicionar_funcionario():
    """Rota para adicionar um novo funcionário."""
    nome = request.form['nome'].strip()
    data_admissao = request.form['data_admissao'].strip()
    data_aniversario = request.form['data_aniversario'].strip()
    data_retorno_licenca = request.form.get('data_retorno_licenca', '').strip()

    # Validação de campos obrigatórios
    if not nome or not data_admissao or not data_aniversario:
        return jsonify({"success": False, "message": "Nome, Data de Admissão e Aniversário são obrigatórios."}), 400

    # Validação de formato de data (DD/MM/AAAA)
    if not validar_data_formato(data_admissao):
        return jsonify({"success": False, "message": "Data de Admissão inválida. Use DD/MM/AAAA."}), 400
    if not validar_data_formato(data_aniversario):
        return jsonify({"success": False, "message": "Data de Aniversário inválida. Use DD/MM/AAAA."}), 400
    if data_retorno_licenca and not validar_data_formato(data_retorno_licenca):
        return jsonify({"success": False, "message": "Data de Retorno de Licença inválida. Use DD/MM/AAAA ou deixe em branco."}), 400

    data_retorno_licenca = data_retorno_licenca if data_retorno_licenca else None

    try:
        insert_funcionario(nome, data_admissao, data_aniversario, data_retorno_licenca)
        return jsonify({"success": True, "message": "Pessoa registrada com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao registrar: {str(e)}"}), 500

@app.route('/get_funcionario/<int:funcionario_id>', methods=['GET'])
def get_funcionario_json(funcionario_id):
    """Retorna os dados de um funcionário em formato JSON para edição."""
    funcionario = get_funcionario_by_id(funcionario_id)
    if funcionario:
        return jsonify(dict(funcionario))
    return jsonify({"success": False, "message": "Funcionário não encontrado."}), 404

@app.route('/editar_funcionario', methods=['POST'])
def editar_funcionario():
    """Rota para editar um funcionário existente."""
    funcionario_id = request.form.get('id_editar')
    nome = request.form['nome_editar'].strip()
    data_admissao = request.form['data_admissao_editar'].strip()
    data_aniversario = request.form['data_aniversario_editar'].strip()
    data_retorno_licenca = request.form.get('data_retorno_licenca_editar', '').strip()

    if not funcionario_id or not nome or not data_admissao or not data_aniversario:
        return jsonify({"success": False, "message": "Todos os campos obrigatórios devem ser preenchidos para edição."}), 400

    if not validar_data_formato(data_admissao):
        return jsonify({"success": False, "message": "Data de Admissão inválida. Use DD/MM/AAAA."}), 400
    if not validar_data_formato(data_aniversario):
        return jsonify({"success": False, "message": "Data de Aniversário inválida. Use DD/MM/AAAA."}), 400
    if data_retorno_licenca and not validar_data_formato(data_retorno_licenca):
        return jsonify({"success": False, "message": "Data de Retorno de Licença inválida. Use DD/MM/AAAA ou deixe em branco."}), 400

    data_retorno_licenca = data_retorno_licenca if data_retorno_licenca else None

    try:
        update_funcionario(funcionario_id, nome, data_admissao, data_aniversario, data_retorno_licenca)
        return jsonify({"success": True, "message": "Pessoa atualizada com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao atualizar: {str(e)}"}), 500

@app.route('/deletar_funcionario/<int:funcionario_id>', methods=['POST'])
def deletar_funcionario(funcionario_id):
    """Rota para deletar um funcionário."""
    try:
        delete_funcionario(funcionario_id)
        return jsonify({"success": True, "message": "Pessoa deletada com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao deletar: {str(e)}"}), 500

def validar_data_formato(data_str):
    """Valida se a string é uma data no formato DD/MM/AAAA."""
    try:
        datetime.datetime.strptime(data_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

if __name__ == '__main__':
    # Isso pode ser útil para ver se o scheduler está funcionando
    # Ao iniciar o app, ele pode chamar a função delete_licenca_passada imediatamente
    # para garantir que ela roda pelo menos uma vez no início, além do agendamento diário.
    # Comentar ou remover em produção se não desejar isso.
    with app.app_context():
        delete_licenca_passada()
    app.run(debug=True)