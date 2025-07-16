# app.py
from flask import Flask, render_template, request, jsonify
from database import insert_funcionario, get_all_funcionarios, create_table, get_funcionario_by_id, update_funcionario, delete_funcionario, delete_licenca_passada
import datetime
from flask_apscheduler import APScheduler

# --- Importações para E-mail ---
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# --- Configurações de E-mail (Lidas das VARIÁVEIS DE AMBIENTE!) ---
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

# --- Lógica de Verificação de Datas Diária (15 e 10 dias antes) ---
# Agendado para rodar diariamente às 7 da manhã.
@scheduler.task('cron', id='check_daily_notifications', hour=7, minute=0)
def check_daily_notifications_job():
    with app.app_context():
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificação de datas diárias para notificação...")
        hoje = datetime.date.today()
        print(f"DEBUG_DIARIO: Data atual (hoje): {hoje.strftime('%d/%m/%Y')}")

        funcionarios = get_all_funcionarios()
        delete_licenca_passada() # Limpa licenças passadas antes de notificar

        destinatarios_gestor = LISTA_EMAILS_GESTOR
        if not destinatarios_gestor:
            print("ERRO_DIARIO: E-mail(s) do gestor não configurado(s). Notificações diárias não enviadas.")
            return

        # Dicionário para consolidar eventos por data de notificação e tipo de evento
        # Chave: (data_evento, tipo_evento_notificacao)
        # Valor: lista de nomes de funcionários
        eventos_para_notificar = {}
        # Ex: {(datetime.date(2025, 7, 31), 'aniversario'): ['Maria Clara', 'João'],
        #      (datetime.date(2025, 8, 1), 'admissao'): ['Pedro']}

        for func in funcionarios:
            nome = func['nome']
            data_admissao_str = func['data_admissao']
            data_aniversario_str = func['data_aniversario']
            data_retorno_licenca_str = func['data_retorno_licenca']

            print(f"DEBUG_DIARIO: Processando {nome}. Admissão: {data_admissao_str}, Aniversário: {data_aniversario_str}, Licença: {data_retorno_licenca_str}")

            # --- Notificação de Aniversário (15 ou 10 dias antes) ---
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                # Ajusta para o ano corrente ou próximo ano
                aniversario_este_ano = aniversario_data_obj.replace(year=hoje.year)
                if aniversario_este_ano < hoje:
                    aniversario_este_ano = aniversario_data_obj.replace(year=hoje.year + 1)
                dias_para_aniversario = (aniversario_este_ano - hoje).days

                if dias_para_aniversario in [15, 10]:
                    chave = (aniversario_este_ano, f"aniversário ({dias_para_aniversario} dias)")
                    if chave not in eventos_para_notificar:
                        eventos_para_notificar[chave] = []
                    eventos_para_notificar[chave].append(nome)
                    print(f"DEBUG_DIARIO: Aniversário de {nome} (em {dias_para_aniversario} dias) adicionado para consolidação.")
            except ValueError:
                print(f"AVISO_DIARIO: Formato de data de aniversário inválido para {nome}: {data_aniversario_str}")


            # --- Notificação de Admissão (15 ou 10 dias antes) ---
            try:
                admissao_data_obj = datetime.datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
                # Ajusta para o ano corrente ou próximo ano
                admissao_este_ano = admissao_data_obj.replace(year=hoje.year)
                if admissao_este_ano < hoje:
                    admissao_este_ano = admissao_data_obj.replace(year=hoje.year + 1)
                dias_para_admissao = (admissao_este_ano - hoje).days

                if dias_para_admissao in [15, 10]:
                    chave = (admissao_este_ano, f"admissão ({dias_para_admissao} dias)")
                    if chave not in eventos_para_notificar:
                        eventos_para_notificar[chave] = []
                    eventos_para_notificar[chave].append(nome)
                    print(f"DEBUG_DIARIO: Admissão de {nome} (em {dias_para_admissao} dias) adicionado para consolidação.")
            except ValueError:
                print(f"AVISO_DIARIO: Formato de data de admissão inválido para {nome}: {data_admissao_str}")

            # --- Notificação de Retorno de Licença (15 ou 10 dias antes) ---
            if data_retorno_licenca_str:
                try:
                    licenca_data_obj = datetime.datetime.strptime(data_retorno_licenca_str, '%d/%m/%Y').date()
                    dias_para_licenca = (licenca_data_obj - hoje).days

                    if dias_para_licenca in [15, 10]:
                        chave = (licenca_data_obj, f"retorno de licença ({dias_para_licenca} dias)")
                        if chave not in eventos_para_notificar:
                            eventos_para_notificar[chave] = []
                        eventos_para_notificar[chave].append(nome)
                        print(f"DEBUG_DIARIO: Retorno de licença de {nome} (em {dias_para_licenca} dias) adicionado para consolidação.")
                except ValueError:
                    print(f"AVISO_DIARIO: Formato de data de retorno de licença inválido para {nome}: {data_retorno_licenca_str}")

        # --- Enviar E-mails Consolidados para Notificações Diárias ---
        if not eventos_para_notificar:
            print("DEBUG_DIARIO: Nenhuma data para notificação diária encontrada.")
        else:
            for (data_evento, tipo_evento_notificacao), nomes_funcionarios in eventos_para_notificar.items():
                lista_nomes = ", ".join(nomes_funcionarios)
                assunto = f"Lembrete RH: {tipo_evento_notificacao.capitalize()} de {lista_nomes.replace(', ', ' e ', -1)}"
                corpo = f"""
                <html>
                <body>
                    <p>Olá Gestor(a)s,</p>
                    <p>Um(a) ou mais evento(s) importante(s) se aproxima(m):</p>
                    <ul>
                        <li>Faltam <b>{tipo_evento_notificacao.split('(')[1].replace(')', '')}</b> para o(s) {tipo_evento_notificacao.split('(')[0].strip()} de: <b>{lista_nomes}</b></li>
                        <li>Data do Evento: <b>{data_evento.strftime('%d/%m/%Y')}</b></li>
                    </ul>
                    <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
                </body>
                </html>
                """
                enviar_email(destinatarios_gestor, assunto, corpo)
                print(f"DEBUG_DIARIO: E-mail diário consolidado enviado para {tipo_evento_notificacao} em {data_evento} para: {lista_nomes}")

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificação de datas diárias concluída.")

# --- Lógica de Verificação de Datas Mensal (Dia 1 do Mês) ---
# Agendado para rodar no dia 1 de cada mês às 7 da manhã.
@scheduler.task('cron', id='send_monthly_summary', day=1, hour=7, minute=0)
def send_monthly_summary_job():
    with app.app_context():
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando envio de resumo mensal de datas importantes...")
        hoje = datetime.date.today()
        proximo_mes = hoje.replace(day=1) + datetime.timedelta(days=32) # Garante ir para o próximo mês
        mes_a_analisar = proximo_mes if hoje.day != 1 else hoje # Se não é dia 1, pega o próximo mês. Se é dia 1, pega o mês atual.

        # Ajusta para garantir que pegue o mês correto quando a tarefa é agendada para o dia 1
        if hoje.day == 1:
            mes_analise_num = hoje.month
            ano_analise_num = hoje.year
        else: # Para testar manualmente (e para o agendamento real) sem mudar o dia 1 no cron, vamos pegar o próximo mês.
              # Se esta função SÓ roda no dia 1, a lógica acima de hoje.day==1 é suficiente
              # Mas para acionamento manual queira o próximo mês para popular
            mes_analise_num = hoje.month + 1 if hoje.month < 12 else 1
            ano_analise_num = hoje.year if hoje.month < 12 else hoje.year + 1

        print(f"DEBUG_MENSAL: Mês/Ano de análise para resumo: {mes_analise_num:02d}/{ano_analise_num}")

        funcionarios = get_all_funcionarios()

        destinatarios_gestor = LISTA_EMAILS_GESTOR
        if not destinatarios_gestor:
            print("ERRO_MENSAL: E-mail(s) do gestor não configurado(s). Resumo mensal não enviado.")
            return

        # Dicionário para consolidar eventos por data específica do mês
        # Chave: datetime.date (data exata do evento)
        # Valor: lista de strings (descrição do evento, ex: "Aniversário de João", "Admissão de Maria")
        resumo_mensal_eventos = {}

        for func in funcionarios:
            nome = func['nome']
            data_admissao_str = func['data_admissao']
            data_aniversario_str = func['data_aniversario']
            data_retorno_licenca_str = func['data_retorno_licenca']

            # --- Aniversários do Mês ---
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                if aniversario_data_obj.month == mes_analise_num:
                    data_completa_evento = aniversario_data_obj.replace(year=ano_analise_num)
                    if data_completa_evento not in resumo_mensal_eventos:
                        resumo_mensal_eventos[data_completa_evento] = []
                    resumo_mensal_eventos[data_completa_evento].append(f"Aniversário de {nome}")
                    print(f"DEBUG_MENSAL: Aniversário de {nome} em {data_completa_evento.strftime('%d/%m')} adicionado ao resumo mensal.")
            except ValueError:
                print(f"AVISO_MENSAL: Formato de data de aniversário inválido para {nome}: {data_aniversario_str}")

            # --- Admissões do Mês ---
            try:
                admissao_data_obj = datetime.datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
                if admissao_data_obj.month == mes_analise_num:
                    data_completa_evento = admissao_data_obj.replace(year=ano_analise_num)
                    if data_completa_evento not in resumo_mensal_eventos:
                        resumo_mensal_eventos[data_completa_evento] = []
                    resumo_mensal_eventos[data_completa_evento].append(f"Aniversário de Admissão de {nome}")
                    print(f"DEBUG_MENSAL: Admissão de {nome} em {data_completa_evento.strftime('%d/%m/%Y')} adicionada ao resumo mensal.")
            except ValueError:
                print(f"AVISO_MENSAL: Formato de data de admissão inválido para {nome}: {data_admissao_str}")

            # --- Retorno de Licença do Mês (se existir) ---
            if data_retorno_licenca_str:
                try:
                    licenca_data_obj = datetime.datetime.strptime(data_retorno_licenca_str, '%d/%m/%Y').date()
                    if licenca_data_obj.month == mes_analise_num and licenca_data_obj.year == ano_analise_num: # Licença é data específica
                        if licenca_data_obj not in resumo_mensal_eventos:
                            resumo_mensal_eventos[licenca_data_obj] = []
                        resumo_mensal_eventos[licenca_data_obj].append(f"Retorno de Licença de {nome}")
                        print(f"DEBUG_MENSAL: Retorno de licença de {nome} em {licenca_data_obj.strftime('%d/%m/%Y')} adicionado ao resumo mensal.")
                except ValueError:
                    print(f"AVISO_MENSAL: Formato de data de retorno de licença inválido para {nome}: {data_retorno_licenca_str}")

        # --- Enviar E-mail de Resumo Mensal ---
        if not resumo_mensal_eventos:
            print(f"DEBUG_MENSAL: Nenhum evento encontrado para o mês {mes_analise_num:02d}/{ano_analise_num}.")
            assunto = f"Resumo RH: Nenhuma Data Importante para {datetime.date(ano_analise_num, mes_analise_num, 1).strftime('%B/%Y')}"
            corpo_html = f"""
            <html><body>
                <p>Olá Gestor(a)s,</p>
                <p>Não há datas importantes agendadas para {datetime.date(ano_analise_num, mes_analise_num, 1).strftime('%B de %Y')}.</p>
                <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
            </body></html>
            """
        else:
            assunto = f"Resumo RH: Datas Importantes para {datetime.date(ano_analise_num, mes_analise_num, 1).strftime('%B/%Y')}"
            corpo_eventos = []
            # Ordena os eventos por data
            for data_evento in sorted(resumo_mensal_eventos.keys()):
                eventos_do_dia = resumo_mensal_eventos[data_evento]
                corpo_eventos.append(f"<li><b>{data_evento.strftime('%d/%m')}</b>: {'; '.join(eventos_do_dia)}</li>")

            corpo_html = f"""
            <html>
            <body>
                <p>Olá Gestor(a)s,</p>
                <p>Segue o resumo das datas importantes para <b>{datetime.date(ano_analise_num, mes_analise_num, 1).strftime('%B de %Y')}</b>:</p>
                <ul>
                    {''.join(corpo_eventos)}
                </ul>
                <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
            </body>
            </html>
            """
        enviar_email(destinatarios_gestor, assunto, corpo_html)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Envio de resumo mensal concluído.")

# --- Rota temporária para teste manual do job (para qualquer job) ---
@app.route('/testar_notificacao_agora/<job_id>', methods=['GET'])
def trigger_notification_test(job_id):
    with app.app_context():
        # Encontra o job pelo ID e executa
        job = scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.datetime.now()) # Força a execução imediata na próxima checagem do scheduler
            print(f"DEBUG: Job '{job_id}' marcado para execução imediata.")
            return jsonify({"message": f"Job '{job_id}' marcado para execução imediata. Verifique os logs do Railway e sua caixa de e-mail."})
        else:
            return jsonify({"message": f"Job '{job_id}' não encontrado."}), 404

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
with app.app_context():
    create_table()

if __name__ == '__main__':
    app.run(debug=True)