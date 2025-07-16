# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import insert_funcionario, get_all_funcionarios, create_table, get_funcionario_by_id, update_funcionario, delete_funcionario, delete_licenca_passada
import datetime
from flask_apscheduler import APScheduler

# --- Importações para E-mail (do notification_worker.py) ---
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# --- Configurações de E-mail (VÃO PARA AS VARIÁVEIS DE AMBIENTE DO SERVIÇO 'web'!) ---
EMAIL_SENDER = os.environ.get("EMAIL_SENDER", "seu_email_para_envio@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "sua_senha_de_aplicativo_do_gmail")
MANAGER_EMAILS_STR = os.environ.get("EMAIL_MANAGER", "email_do_gestor@exemplo.com")
LISTA_EMAILS_GESTOR = [e.strip() for e in MANAGER_EMAILS_STR.split(',') if e.strip()]

EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587

def enviar_email(destinatarios_email, assunto, corpo_html):
    """
    Função para enviar e-mail via SMTP do Gmail para múltiplos destinatários.
    """
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("Erro: Credenciais de e-mail do remetente não configuradas. Verifique as variáveis de ambiente EMAIL_SENDER e EMAIL_PASSWORD.")
        return False
    if not destinatarios_email:
        print("Erro: Nenhum e-mail de destinatário especificado.")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_SENDER
    msg["Subject"] = assunto
    msg["To"] = ", ".join(destinatarios_email)

    msg.attach(MIMEText(corpo_html, "html"))

    try:
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg, from_addr=EMAIL_SENDER, to_addrs=destinatarios_email)
        print(f"E-mail enviado com sucesso para {', '.join(destinatarios_email)} - Assunto: '{assunto}'.")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"Erro de autenticação SMTP para {EMAIL_SENDER}. Verifique se a senha de aplicativo está correta e se a Verificação em Duas Etapas está ativa.")
        return False
    except Exception as e:
        print(f"Erro inesperado ao enviar e-mail para {', '.join(destinatarios_email)}: {e}")
        return False

# --- Lógica de Verificação de Datas (MOVIDA DO notification_worker.py) ---
@scheduler.task('cron', id='check_and_notify_dates', hour=0, minute=0) # Roda à meia-noite (00:00)
def check_and_notify_dates_job():
    # Esta função agora precisa de um app_context para acessar o banco de dados via Flask
    with app.app_context():
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificação de datas para notificação por e-mail (agendado)...")
        hoje = datetime.date.today()
        print(f"DEBUG: Data atual (hoje): {hoje.strftime('%d/%m/%Y')}")

        funcionarios = get_all_funcionarios()

        if not funcionarios:
            print("DEBUG: NENHUM FUNCIONÁRIO ENCONTRADO NO BANCO DE DADOS.")
        else:
            print(f"DEBUG: {len(funcionarios)} funcionários encontrados no banco de dados.")
            for func in funcionarios:
                print(f"DEBUG: Processando funcionário: ID={func['id']}, Nome={func['nome']}, Admissão={func['data_admissao']}, Aniversário={func['data_aniversario']}, Licença={func['data_retorno_licenca']}")

        delete_licenca_passada() # Esta função deve ser chamada dentro do app_context

        destinatarios_gestor = LISTA_EMAILS_GESTOR
        if not destinatarios_gestor:
            print("ERRO CRÍTICO: E-mail(s) do gestor (EMAIL_MANAGER) não configurado(s) ou inválido(s). As notificações não serão enviadas.")
            return

        for func in funcionarios:
            nome = func['nome']
            data_admissao_str = func['data_admissao']
            data_aniversario_str = func['data_aniversario']
            data_retorno_licenca_str = func['data_retorno_licenca']

            # Notificação de Aniversário
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                if aniversario_data_obj.month == hoje.month: # <-- Lógica de teste "mês atual"
                    print(f"DEBUG: *** ACIONADO (ANIVERSÁRIO - MÊS ATUAL) PARA {nome} em {aniversario_data_obj.strftime('%d/%m')} ***")
                    assunto = f"Lembrete RH: Aniversário de {nome} neste mês!"
                    corpo = f"""
                    <html>
                    <body>
                        <p>Olá Gestor(a)s,</p>
                        <p>É um prazer informar que faltam {aniversario_data_obj.day - hoje.day} dias para o aniversário de <b>{nome}</b>!</p>
                        <p>A data especial é <b>{aniversario_data_obj.strftime('%d/%m')}</b>.</p>
                        <p>Vamos celebrar juntos!</p>
                        <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
                    </body>
                    </html>
                    """
                    enviar_email(destinatarios_gestor, assunto, corpo)
            except ValueError:
                print(f"AVISO: Formato de data de aniversário inválido para {nome}: {data_aniversario_str}")

            # Notificação de Admissão
            try:
                admissao_data_obj = datetime.datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
                if admissao_data_obj.month == hoje.month: # <-- Lógica de teste "mês atual"
                    print(f"DEBUG: *** ACIONADO (ADMISSÃO - MÊS ATUAL) PARA {nome} em {admissao_data_obj.strftime('%d/%m/%Y')} ***")
                    assunto = f"Lembrete RH: Aniversário de Admissão de {nome} neste mês!"
                    corpo = f"""
                    <html>
                    <body>
                        <p>Olá Gestor(a)s,</p>
                        <p>Faltam {admissao_data_obj.day - hoje.day} dias para o aniversário de admissão de <b>{nome}</b>!</p>
                        <p>Ele(a) foi admitido(a) em <b>{admissao_data_obj.strftime('%d/%m/%Y')}</b>.</p>
                        <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
                    </body>
                    </html>
                    """
                    enviar_email(destinatarios_gestor, assunto, corpo)
            except ValueError:
                print(f"AVISO: Formato de data de admissão inválido para {nome}: {data_admissao_str}")

            # Notificação de Retorno de Licença
            if data_retorno_licenca_str:
                try:
                    licenca_data_obj = datetime.datetime.strptime(data_retorno_licenca_str, '%d/%m/%Y').date()
                    if licenca_data_obj.month == hoje.month: # <-- Lógica de teste "mês atual"
                        print(f"DEBUG: *** ACIONADO (LICENÇA - MÊS ATUAL) PARA {nome} em {licenca_data_obj.strftime('%d/%m/%Y')} ***")
                        assunto = f"Lembrete RH: Retorno de Licença de {nome} neste mês!"
                        corpo = f"""
                        <html>
                        <body>
                            <p>Olá Gestor(a)s,</p>
                            <p>Faltam {licenca_data_obj.day - hoje.day} dias para o retorno de licença de <b>{nome}</b>!</p>
                            <p>A data prevista de retorno é <b>{licenca_data_obj.strftime('%d/%m/%Y')}</b>.</p>
                            <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
                        </body>
                        </html>
                        """
                        enviar_email(destinatarios_gestor, assunto, corpo)
                except ValueError:
                    print(f"AVISO: Formato de data de retorno de licença inválido para {nome}: {data_retorno_licenca_str}")
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificação de datas para e-mail concluída.")

# --- As rotas Flask existentes ---
@app.route('/')
def index():
    funcionarios = get_all_funcionarios()
    return render_template('index.html', funcionarios=funcionarios)

@app.route('/adicionar_funcionario', methods=['POST'])
def adicionar_funcionario():
    nome = request.form['nome'].strip()
    data_admissao = request.form['data_admissao'].strip()
    data_aniversario = request.form['data_aniversario'].strip()
    data_retorno_licenca = request.form.get('data_retorno_licenca', '').strip()

    if not nome or not data_admissao or not data_aniversario:
        return jsonify({"success": False, "message": "Nome, Data de Admissão e Aniversário são obrigatórios."}), 400

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
    funcionario = get_funcionario_by_id(funcionario_id)
    if funcionario:
        return jsonify(dict(funcionario))
    return jsonify({"success": False, "message": "Funcionário não encontrado."}), 404

@app.route('/editar_funcionario', methods=['POST'])
def editar_funcionario():
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
    try:
        delete_funcionario(funcionario_id)
        return jsonify({"success": True, "message": "Pessoa deletada com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao deletar: {str(e)}"}), 500

def validar_data_formato(data_str):
    try:
        datetime.datetime.strptime(data_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

# --- Inicialização da Tabela no Início do Aplicativo ---
# Esta função cria a tabela no banco de dados quando o Flask app inicia.
# Garante que o banco seja criado no volume.
with app.app_context():
    create_table()

if __name__ == '__main__':
    # Remover o `delete_licenca_passada()` daqui se o scheduler já está rodando ele
    # no `check_and_notify_dates_job`
    app.run(debug=True)