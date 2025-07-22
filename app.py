# app.py
from flask import Flask, render_template, request, jsonify
from database import insert_funcionario, get_all_funcionarios, create_table, get_funcionario_by_id, update_funcionario, delete_funcionario, delete_licenca_passada, insert_cliente, get_all_clientes, get_cliente_by_id, update_cliente, delete_cliente
import datetime
import os # Necessário para os.environ.get
# REMOVIDO: import csv # Não é mais necessário para importação de CSV
# REMOVIDO: import io # Não é mais necessário para importação de CSV
import smtplib # Para enviar e-mails
from email.mime.text import MIMEText # Para corpo de e-mail HTML
from email.mime.multipart import MIMEMultipart # Para e-mails multipart
from flask_apscheduler import APScheduler # Para agendamento de tarefas

# Dicionário para mapear números dos meses para nomes em português (solução robusta)
MESES_EM_PORTUGUES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}

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
@scheduler.task('cron', id='check_daily_notifications', hour=7, minute=0)
def check_daily_notifications_job():
    with app.app_context():
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificação de datas diárias para notificação...")
        hoje = datetime.date.today()
        print(f"DEBUG_DIARIO: Data atual (hoje): {hoje.strftime('%d/%m/%Y')}")

        funcionarios = get_all_funcionarios()
        clientes = get_all_clientes() # NOVO: Obtém todos os clientes
        delete_licenca_passada()

        destinatarios_gestor = LISTA_EMAILS_GESTOR
        if not destinatarios_gestor:
            print("ERRO_DIARIO: E-mail(s) do gestor não configurado(s). Notificações diárias não enviadas.")
            return

        # NOVO: eventos_para_notificar agora armazena dicionários com 'nome' e 'anos_contajur' (opcional)
        # Chave: (data_do_evento, tipo_base_do_evento_limpo, dias_restantes)
        # Valor: lista de {'nome': str, 'anos_contajur': int | None}
        eventos_para_notificar = {}

        # --- Processa Funcionários ---
        for func in funcionarios:
            nome = func['nome']
            data_admissao_str = func['data_admissao']
            data_aniversario_str = func['data_aniversario']
            data_retorno_licenca_str = func['data_retorno_licenca']

            print(f"DEBUG_DIARIO: Processando FUNCIONÁRIO {nome}. Admissão: {data_admissao_str}, Aniversário: {data_aniversario_str}, Licença: {data_retorno_licenca_str}")

            # Notificação de Aniversário (15 ou 10 dias antes)
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                aniversario_este_ano = aniversario_data_obj.replace(year=hoje.year)
                if aniversario_este_ano < hoje:
                    aniversario_este_ano = aniversario_data_obj.replace(year=hoje.year + 1)
                dias_para_aniversario = (aniversario_este_ano - hoje).days

                if dias_para_aniversario in [15, 10]:
                    chave = (aniversario_este_ano, f"aniversário de funcionário", dias_para_aniversario) # Tipo base
                    if chave not in eventos_para_notificar:
                        eventos_para_notificar[chave] = []
                    eventos_para_notificar[chave].append({'nome': nome, 'anos_contajur': None}) # Aniversário não tem "anos de Contajur"
                    print(f"DEBUG_DIARIO: Aniversário de funcionário {nome} (em {dias_para_aniversario} dias) adicionado para consolidação.")
            except ValueError:
                print(f"AVISO_DIARIO: Formato de data de aniversário de funcionário inválido para {nome}: {data_aniversario_str}")


            # Notificação de Admissão (15 ou 10 dias antes)
            try:
                admissao_data_obj = datetime.datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
                admissao_este_ano = admissao_data_obj.replace(year=hoje.year)
                if admissao_este_ano < hoje:
                    admissao_este_ano = admissao_data_obj.replace(year=hoje.year + 1)
                dias_para_admissao = (admissao_este_ano - hoje).days

                if dias_para_admissao in [15, 10]:
                    anos_de_contajur = hoje.year - admissao_data_obj.year # Calcula os anos de Contajur
                    chave = (admissao_este_ano, f"admissão de funcionário", dias_para_admissao) # Tipo base
                    if chave not in eventos_para_notificar:
                        eventos_para_notificar[chave] = []
                    eventos_para_notificar[chave].append({'nome': nome, 'anos_contajur': anos_de_contajur})
                    print(f"DEBUG_DIARIO: Admissão de funcionário {nome} (em {dias_para_admissao} dias, {anos_de_contajur} anos de Contajur) adicionado para consolidação.")
            except ValueError:
                print(f"AVISO_DIARIO: Formato de data de admissão de funcionário inválido para {nome}: {data_admissao_str}")

            # Notificação de Retorno de Licença (15 ou 10 dias antes)
            if data_retorno_licenca_str:
                try:
                    licenca_data_obj = datetime.datetime.strptime(data_retorno_licenca_str, '%d/%m/%Y').date()
                    dias_para_licenca = (licenca_data_obj - hoje).days

                    if dias_para_licenca in [15, 10]:
                        chave = (licenca_data_obj, f"retorno de licença de funcionário", dias_para_licenca) # Tipo base
                        if chave not in eventos_para_notificar:
                            eventos_para_notificar[chave] = []
                        eventos_para_notificar[chave].append({'nome': nome, 'anos_contajur': None}) # Licença não tem "anos de Contajur"
                        print(f"DEBUG_DIARIO: Retorno de licença de funcionário {nome} (em {dias_para_licenca} dias) adicionado para consolidação.")
                except ValueError:
                    print(f"AVISO_DIARIO: Formato de data de retorno de licença de funcionário inválido para {nome}: {data_retorno_licenca_str}")

        # --- Processa Clientes ---
        for cliente in clientes:
            nome = cliente['nome']
            data_aniversario_str = cliente['data_aniversario']

            print(f"DEBUG_DIARIO: Processando CLIENTE {nome}. Aniversário: {data_aniversario_str}")

            # Notificação de Aniversário de Cliente (15 ou 10 dias antes)
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                aniversario_este_ano = aniversario_data_obj.replace(year=hoje.year)
                if aniversario_este_ano < hoje:
                    aniversario_este_ano = aniversario_data_obj.replace(year=hoje.year + 1)
                dias_para_aniversario = (aniversario_este_ano - hoje).days

                if dias_para_aniversario in [15, 10]:
                    anos_de_contajur = hoje.year - aniversario_data_obj.year # Calcula os anos de Contajur
                    chave = (aniversario_este_ano, f"aniversário de cliente", dias_para_aniversario) # Tipo base
                    if chave not in eventos_para_notificar:
                        eventos_para_notificar[chave] = []
                    eventos_para_notificar[chave].append({'nome': nome, 'anos_contajur': anos_de_contajur})
                    print(f"DEBUG_DIARIO: Aniversário de cliente {nome} (em {dias_para_aniversario} dias, {anos_de_contajur} anos de Contajur) adicionado para consolidação.")
            except ValueError:
                print(f"AVISO_DIARIO: Formato de data de aniversário de cliente inválido para {nome}: {data_aniversario_str}")


        # --- Enviar E-mails Consolidados para Notificações Diárias ---
        if not eventos_para_notificar:
            print("DEBUG_DIARIO: Nenhuma data para notificação diária encontrada.")
        else:
            # Itera sobre os eventos agrupados
            for (data_evento, tipo_base_evento, dias_restantes), detalhes_nomes_list in eventos_para_notificar.items():
                # Extrai apenas os nomes para a lista e o assunto
                nomes_apenas = [d['nome'] for d in detalhes_nomes_list]
                lista_nomes_str = ", ".join(nomes_apenas)

                # Formata o assunto para singular/plural
                if len(nomes_apenas) > 1:
                   assunto_nomes = f"{', '.join(nomes_apenas[:-1])} e {nomes_apenas[-1]}"
                else:
                   assunto_nomes = nomes_apenas[0]

                assunto = f"Lembrete RH: {tipo_base_evento.capitalize()} de {assunto_nomes}"

                # Lógica para adicionar a linha "X anos de Contajur"
                anos_contajur_linha = ""
                if tipo_base_evento == "admissão de funcionário":
                    if len(detalhes_nomes_list) == 1:
                        anos = detalhes_nomes_list[0]['anos_contajur']
                        # Texto EXATO solicitado para admissão de funcionário
                        anos_contajur_linha = f"<li>Irá completar <b>{anos} anos</b> de Contajur</li>"
                    else:
                        # Para múltiplos, usar plural genérico
                        anos_contajur_linha = "<li>Irá(ão) completar seus respectivos anos de Contajur</li>"
                elif tipo_base_evento == "aniversário de cliente":
                    if len(detalhes_nomes_list) == 1:
                        anos = detalhes_nomes_list[0]['anos_contajur']
                        # Texto EXATO solicitado para aniversário de cliente
                        anos_contajur_linha = f"<li>O cliente vai fazer <b>{anos} anos</b> de Contajur</li>"
                    else:
                        # Para múltiplos, usar plural genérico
                        anos_contajur_linha = "<li>Os clientes farão seus respectivos anos de Contajur</li>"

                corpo = f"""
                <html>
                <body>
                    <p>Olá Gestores,</p>
                    <p>Um(a) ou mais evento(s) importante(s) se aproxima(m):</p>
                    <ul>
                        <li>Faltam <b>{dias_restantes} dias</b> para o(s) {tipo_base_evento} de: <b>{lista_nomes_str}</b></li>
                        <li>Data do Evento: <b>{data_evento.strftime('%d/%m/%Y')}</b></li>
                        {anos_contajur_linha}
                    </ul>
                    <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
                </body>
                </html>
                """
                enviar_email(destinatarios_gestor, assunto, corpo)
                print(f"DEBUG_DIARIO: E-mail diário consolidado enviado para {tipo_base_evento} em {data_evento} para: {lista_nomes_str}")

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificação de datas diárias concluída.")

# --- Lógica de Verificação de Datas Mensal (Dia 1 do Mês) ---
@scheduler.task('cron', id='send_monthly_summary', day=1, hour=7, minute=0)
def send_monthly_summary_job():
    with app.app_context():
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando envio de resumo mensal de datas importantes...")
        hoje = datetime.date.today()

        mes_analise_data = hoje
        if hoje.day != 1:
            mes_analise_data = (hoje.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

        mes_analise_num = mes_analise_data.month
        ano_analise_num = mes_analise_data.year

        nome_do_mes_pt = MESES_EM_PORTUGUES.get(mes_analise_num, f"Mês {mes_analise_num}")


        print(f"DEBUG: Mês/Ano de análise para resumo: {nome_do_mes_pt.capitalize()}/{ano_analise_num}")

        funcionarios = get_all_funcionarios()
        clientes = get_all_clientes()

        destinatarios_gestor = LISTA_EMAILS_GESTOR
        if not destinatarios_gestor:
            print("ERRO: E-mail(s) do gestor não configurado(s). Resumo mensal não enviado.")
            return

        resumo_mensal_eventos = {}

        # --- Processa Funcionários para o Resumo Mensal ---
        for func in funcionarios:
            nome = func['nome']
            data_admissao_str = func['data_admissao']
            data_aniversario_str = func['data_aniversario']
            data_retorno_licenca_str = func['data_retorno_licenca']

            # Aniversários do Mês
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                if aniversario_data_obj.month == mes_analise_num:
                    data_completa_evento = aniversario_data_obj.replace(year=ano_analise_num)
                    if data_completa_evento not in resumo_mensal_eventos:
                        resumo_mensal_eventos[data_completa_evento] = []
                    resumo_mensal_eventos[data_completa_evento].append(f"Aniversário de Funcionário: {nome}")
                    print(f"DEBUG: Aniversário de funcionário {nome} em {data_completa_evento.strftime('%d/%m')} adicionado ao resumo mensal.")
            except ValueError:
                print(f"AVISO: Formato de data de aniversário de funcionário inválido para {nome}: {data_aniversario_str}")

            # Admissões do Mês
            try:
                admissao_data_obj = datetime.datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
                if admissao_data_obj.month == mes_analise_num:
                    data_completa_evento = admissao_data_obj.replace(year=ano_analise_num)
                    if data_completa_evento not in resumo_mensal_eventos:
                        resumo_mensal_eventos[data_completa_evento] = []
                    resumo_mensal_eventos[data_completa_evento].append(f"Aniversário de Admissão de Funcionário: {nome}")
                    print(f"DEBUG: Admissão de funcionário {nome} em {data_completa_evento.strftime('%d/%m/%Y')} adicionada ao resumo mensal.")
            except ValueError:
                print(f"AVISO: Formato de data de admissão de funcionário inválido para {nome}: {data_admissao_str}")

            # Retorno de Licença do Mês (se existir)
            if data_retorno_licenca_str:
                try:
                    licenca_data_obj = datetime.datetime.strptime(data_retorno_licenca_str, '%d/%m/%Y').date()
                    if licenca_data_obj.month == mes_analise_num and licenca_data_obj.year == ano_analise_num:
                        if licenca_data_obj not in resumo_mensal_eventos:
                            resumo_mensal_eventos[licenca_data_obj] = []
                        resumo_mensal_eventos[licenca_data_obj].append(f"Retorno de Licença de Funcionário: {nome}")
                        print(f"DEBUG: Retorno de licença de funcionário {nome} em {licenca_data_obj.strftime('%d/%m/%Y')} adicionado ao resumo mensal.")
                except ValueError:
                    print(f"AVISO: Formato de data de retorno de licença de funcionário inválido para {nome}: {data_retorno_licenca_str}")

        # --- Processa Clientes para o Resumo Mensal ---
        for cliente in clientes:
            nome = cliente['nome']
            data_aniversario_str = cliente['data_aniversario']

            # Aniversários de Clientes do Mês
            try:
                aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
                if aniversario_data_obj.month == mes_analise_num:
                    data_completa_evento = aniversario_data_obj.replace(year=ano_analise_num)
                    if data_completa_evento not in resumo_mensal_eventos:
                        resumo_mensal_eventos[data_completa_evento] = []
                    resumo_mensal_eventos[data_completa_evento].append(f"Aniversário de Cliente: {nome}")
                    print(f"DEBUG: Aniversário de cliente {nome} em {data_completa_evento.strftime('%d/%m')} adicionado ao resumo mensal.")
            except ValueError:
                print(f"AVISO: Formato de data de aniversário de cliente inválido para {nome}: {data_aniversario_str}")


        # --- Enviar E-mail de Resumo Mensal ---
        if not resumo_mensal_eventos:
            print(f"DEBUG: Nenhum evento encontrado para o mês {nome_do_mes_pt}/{ano_analise_num}.")
            assunto = f"Resumo RH: Nenhuma Data Importante para {nome_do_mes_pt.capitalize()}/{ano_analise_num}"
            corpo_html = f"""
            <html><body>
                <p>Olá Gestor(a)s,</p>
                <p>Não há datas importantes agendadas para {nome_do_mes_pt.capitalize()} de {ano_analise_num}.</p>
                <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
            </body></html>
            """
        else:
            assunto = f"Resumo RH: Datas Importantes para {nome_do_mes_pt.capitalize()}/{ano_analise_num}"
            corpo_eventos = []
            for data_evento in sorted(resumo_mensal_eventos.keys()):
                eventos_do_dia = resumo_mensal_eventos[data_evento]
                corpo_eventos.append(f"<li><b>{data_evento.strftime('%d/%m')}</b>: {'; '.join(eventos_do_dia)}</li>")

            corpo_html = f"""
            <html>
            <body>
                <p>Olá Gestor(a)s,</p>
                <p>Segue o resumo das datas importantes para <b>{nome_do_mes_pt.capitalize()} de {ano_analise_num}</b>:</p>
                <ul>
                    {''.join(corpo_eventos)}
                </ul>
                <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
            </body>
            </html>
            """
        enviar_email(destinatarios_gestor, assunto, corpo_html)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Envio de resumo mensal concluído.")

# --- Rota temporária para teste manual do job ---
@app.route('/testar_notificacao_agora/<job_id>', methods=['GET'])
def trigger_notification_test(job_id):
    with app.app_context():
        job = scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.datetime.now())
            print(f"DEBUG: Job '{job_id}' marcado para execução imediata.")
            return jsonify({"message": f"Job '{job_id}' marcado para execução imediata. Verifique os logs do Railway e sua caixa de e-mail."})
        else:
            return jsonify({"message": f"Job '{job_id}' não encontrado."}), 404

# --- As rotas Flask existentes ---
@app.route('/')
def index():
    funcionarios = get_all_funcionarios()
    clientes = get_all_clientes() # NOVO: Passa os clientes para o template
    return render_template('index.html', funcionarios=funcionarios, clientes=clientes) # NOVO: Passa clientes

# --- Rotas para Funcionários (existentes) ---
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

# --- NOVO: Rotas para Clientes ---
@app.route('/adicionar_cliente', methods=['POST'])
def adicionar_cliente():
    nome = request.form['nome_cliente'].strip()
    data_aniversario = request.form['data_aniversario_cliente'].strip()

    if not nome or not data_aniversario:
        return jsonify({"success": False, "message": "Nome e Data de Aniversário do cliente são obrigatórios."}), 400

    if not validar_data_formato(data_aniversario):
        return jsonify({"success": False, "message": "Data de Aniversário do cliente inválida. Use DD/MM/AAAA."}), 400

    try:
        insert_cliente(nome, data_aniversario)
        return jsonify({"success": True, "message": "Cliente registrado com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao registrar cliente: {str(e)}"}), 500

@app.route('/get_cliente/<int:cliente_id>', methods=['GET'])
def get_cliente_json(cliente_id):
    cliente = get_cliente_by_id(cliente_id)
    if cliente:
        return jsonify(dict(cliente))
    return jsonify({"success": False, "message": "Cliente não encontrado."}), 404

@app.route('/editar_cliente', methods=['POST'])
def editar_cliente():
    cliente_id = request.form.get('id_editar_cliente')
    nome = request.form['nome_editar_cliente'].strip()
    data_aniversario = request.form['data_aniversario_editar_cliente'].strip()

    if not cliente_id or not nome or not data_aniversario:
        return jsonify({"success": False, "message": "Todos os campos obrigatórios devem ser preenchidos para edição do cliente."}), 400

    if not validar_data_formato(data_aniversario):
        return jsonify({"success": False, "message": "Data de Aniversário do cliente inválida. Use DD/MM/AAAA."}), 400

    try:
        update_cliente(cliente_id, nome, data_aniversario)
        return jsonify({"success": True, "message": "Cliente atualizado com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao atualizar cliente: {str(e)}"}), 500

@app.route('/deletar_cliente/<int:cliente_id>', methods=['POST'])
def deletar_cliente(cliente_id):
    try:
        delete_cliente(cliente_id)
        return jsonify({"success": True, "message": "Cliente deletado com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro ao deletar cliente: {str(e)}"}), 500


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