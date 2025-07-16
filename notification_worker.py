# notification_worker.py
import sqlite3
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configurações do Banco de Dados ---
DATABASE_NAME = os.path.join("/mnt/data/", "datas_importantes.db")

def connect_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_funcionarios():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, data_admissao, data_aniversario, data_retorno_licenca FROM funcionarios")
    funcionarios = cursor.fetchall()
    conn.close()
    return funcionarios

def delete_licenca_passada():
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
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificação de licenças passadas executada pelo worker.")


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

def verificar_datas_para_notificacao():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando verificação de datas para notificação por e-mail...")
    hoje = datetime.date.today()
    print(f"DEBUG: Data atual (hoje): {hoje.strftime('%d/%m/%Y')}") # DEBUG

    funcionarios = get_all_funcionarios()

    if not funcionarios:
        print("DEBUG: NENHUM FUNCIONÁRIO ENCONTRADO NO BANCO DE DADOS.") # DEBUG
        # Além disso, verifique a persistência do banco de dados (Volume) no Railway!
        # Se os dados não estão sendo salvos ou lidos, esse é o problema.
    else:
        print(f"DEBUG: {len(funcionarios)} funcionários encontrados no banco de dados.") # DEBUG
        for func in funcionarios:
            print(f"DEBUG: Processando funcionário: ID={func['id']}, Nome={func['nome']}, Admissão={func['data_admissao']}, Aniversário={func['data_aniversario']}, Licença={func['data_retorno_licenca']}") # DEBUG

    delete_licenca_passada()

    destinatarios_gestor = LISTA_EMAILS_GESTOR
    if not destinatarios_gestor:
        print("ERRO CRÍTICO: E-mail(s) do gestor (EMAIL_MANAGER) não configurado(s) ou inválido(s). As notificações não serão enviadas.")
        return

    for func in funcionarios:
        nome = func['nome']
        data_admissao_str = func['data_admissao']
        data_aniversario_str = func['data_aniversario']
        data_retorno_licenca_str = func['data_retorno_licenca']

        # --- Teste para Aniversário (qualquer dia do mês atual) ---
        try:
            aniversario_data_obj = datetime.datetime.strptime(data_aniversario_str, '%d/%m/%Y').date()
            # NOTIFICA SE O MÊS DE ANIVERSÁRIO É O MÊS ATUAL
            if aniversario_data_obj.month == hoje.month: # <-- MUDANÇA AQUI PARA TESTE
                print(f"DEBUG: *** ACIONADO (ANIVERSÁRIO - MÊS ATUAL) PARA {nome} em {aniversario_data_obj.strftime('%d/%m')} ***") # DEBUG
                assunto = f"Lembrete RH: Aniversário de {nome} neste mês!"
                corpo = f"""
                <html>
                <body>
                    <p>Olá Gestor(a)s,</p>
                    <p>Faltam {aniversario_data_obj.day - hoje.day} dias para o aniversário de <b>{nome}</b>!</p>
                    <p>A data especial é <b>{aniversario_data_obj.strftime('%d/%m')}</b>.</p>
                    <p>Vamos celebrar juntos!</p>
                    <p>Atenciosamente,<br>Seu Sistema de Notificações de RH</p>
                </body>
                </html>
                """
                enviar_email(destinatarios_gestor, assunto, corpo)
        except ValueError:
            print(f"AVISO: Formato de data de aniversário inválido para {nome}: {data_aniversario_str}")


        # --- Teste para Admissão (qualquer dia do mês atual) ---
        try:
            admissao_data_obj = datetime.datetime.strptime(data_admissao_str, '%d/%m/%Y').date()
            # NOTIFICA SE O MÊS DE ADMISSÃO É O MÊS ATUAL
            if admissao_data_obj.month == hoje.month: # <-- MUDANÇA AQUI PARA TESTE
                print(f"DEBUG: *** ACIONADO (ADMISSÃO - MÊS ATUAL) PARA {nome} em {admissao_data_obj.strftime('%d/%m/%Y')} ***") # DEBUG
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


        # --- Teste para Retorno de Licença (qualquer dia do mês atual) ---
        if data_retorno_licenca_str:
            try:
                licenca_data_obj = datetime.datetime.strptime(data_retorno_licenca_str, '%d/%m/%Y').date()
                # NOTIFICA SE O MÊS DE RETORNO É O MÊS ATUAL
                if licenca_data_obj.month == hoje.month: # <-- MUDANÇA AQUI PARA TESTE
                    print(f"DEBUG: *** ACIONADO (LICENÇA - MÊS ATUAL) PARA {nome} em {licenca_data_obj.strftime('%d/%m/%Y')} ***") # DEBUG
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

if __name__ == "__main__":
    conn = sqlite3.connect(DATABASE_NAME)
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
    conn.commit()
    conn.close()

    verificar_datas_para_notificacao()