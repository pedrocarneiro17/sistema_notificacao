// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Referências para Formulários e Mensagens de Funcionários ---
    const registroFuncionarioForm = document.getElementById('registroFuncionarioForm');
    const mensagemFuncionarioDiv = document.getElementById('mensagemFuncionario');
    const funcionariosTableBody = document.querySelector('#funcionariosTable tbody');
    const editFuncionarioModal = document.getElementById('editFuncionarioModal');
    const editFuncionarioForm = document.getElementById('editFuncionarioForm');
    const mensagemEditarFuncionarioDiv = document.getElementById('mensagemEditarFuncionario');
    const closeFuncionarioModalBtn = document.querySelector('.close-button.funcionario'); // Botão de fechar específico

    // --- Referências para Formulários e Mensagens de Clientes ---
    const registroClienteForm = document.getElementById('registroClienteForm'); // NOVO
    const mensagemClienteDiv = document.getElementById('mensagemCliente'); // NOVO
    const clientesTableBody = document.querySelector('#clientesTable tbody'); // NOVO
    const editClienteModal = document.getElementById('editClienteModal'); // NOVO
    const editClienteForm = document.getElementById('editClienteForm'); // NOVO
    const mensagemEditarClienteDiv = document.getElementById('mensagemEditarCliente'); // NOVO
    const closeClienteModalBtn = document.querySelector('.close-button.cliente'); // NOVO: Botão de fechar específico


    // --- Campos de Data para Formatação Automática ---
    const camposData = [
        document.getElementById('data_admissao'),
        document.getElementById('data_aniversario'),
        document.getElementById('data_retorno_licenca'),
        document.getElementById('data_admissao_editar_funcionario'),
        document.getElementById('data_aniversario_editar_funcionario'),
        document.getElementById('data_retorno_licenca_editar_funcionario'),
        document.getElementById('data_aniversario_cliente'), // NOVO
        document.getElementById('data_aniversario_editar_cliente') // NOVO
    ].filter(Boolean); // Filtra nulls se algum ID não for encontrado

    // --- Função para formatar a data automaticamente (DD/MM/AAAA) ---
    function formatarData(event) {
        let input = event.target;
        let value = input.value.replace(/\D/g, '');

        if (event.inputType === 'deleteContentBackward') {
            input.value = value;
            return;
        }

        if (value.length > 2 && value.length <= 4) {
            value = value.substring(0, 2) + '/' + value.substring(2);
        } else if (value.length > 4) {
            value = value.substring(0, 2) + '/' + value.substring(2, 4) + '/' + value.substring(4, 8);
        }
        input.value = value;
    }

    // --- Atribuir a função de formatação aos campos de data ---
    camposData.forEach(campo => {
        campo.addEventListener('input', formatarData);
    });

    // Função genérica para exibir mensagem
    function showMessage(divElement, message, type) {
        divElement.textContent = message;
        divElement.classList.remove('success', 'error');
        if (type) {
            divElement.classList.add(type);
        }
    }

    // --- Lógica de Registro de Funcionário ---
    registroFuncionarioForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(registroFuncionarioForm);
        showMessage(mensagemFuncionarioDiv, '', '');

        try {
            const response = await fetch('/adicionar_funcionario', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                showMessage(mensagemFuncionarioDiv, result.message, 'success');
                registroFuncionarioForm.reset();
                await carregarTabelas(); // Carrega ambas as tabelas
            } else {
                showMessage(mensagemFuncionarioDiv, result.message, 'error');
            }
        } catch (error) {
            console.error('Erro ao registrar funcionário:', error);
            showMessage(mensagemFuncionarioDiv, 'Erro de comunicação com o servidor.', 'error');
        }
    });

    // --- NOVO: Lógica de Registro de Cliente ---
    registroClienteForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(registroClienteForm);
        showMessage(mensagemClienteDiv, '', '');

        try {
            const response = await fetch('/adicionar_cliente', { // Nova rota
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                showMessage(mensagemClienteDiv, result.message, 'success');
                registroClienteForm.reset();
                await carregarTabelas(); // Carrega ambas as tabelas
            } else {
                showMessage(mensagemClienteDiv, result.message, 'error');
            }
        } catch (error) {
            console.error('Erro ao registrar cliente:', error);
            showMessage(mensagemClienteDiv, 'Erro de comunicação com o servidor.', 'error');
        }
    });


    // --- Lógica de Edição/Exclusão (Geral para Funcionário e Cliente) ---
    // Event listener para ambas as tabelas (funcionários e clientes)
    document.body.addEventListener('click', async (event) => {
        // --- Lógica de Edição ---
        if (event.target.classList.contains('editar-btn')) {
            const id = event.target.dataset.id;
            const type = event.target.dataset.type; // 'funcionario' ou 'cliente'

            if (type === 'funcionario') {
                showMessage(mensagemEditarFuncionarioDiv, '', '');
                try {
                    const response = await fetch(`/get_funcionario/${id}`);
                    const funcionario = await response.json();
                    if (response.ok) {
                        document.getElementById('id_editar_funcionario').value = funcionario.id;
                        document.getElementById('nome_editar_funcionario').value = funcionario.nome;
                        document.getElementById('data_admissao_editar_funcionario').value = funcionario.data_admissao;
                        document.getElementById('data_aniversario_editar_funcionario').value = funcionario.data_aniversario;
                        document.getElementById('data_retorno_licenca_editar_funcionario').value = funcionario.data_retorno_licenca || '';
                        editFuncionarioModal.style.display = 'flex';
                    } else {
                        showMessage(mensagemFuncionarioDiv, funcionario.message, 'error');
                    }
                } catch (error) {
                    console.error('Erro ao buscar funcionário para edição:', error);
                    showMessage(mensagemFuncionarioDiv, 'Erro ao carregar dados do funcionário para edição.', 'error');
                }
            } else if (type === 'cliente') { // NOVO: Lógica de Edição para Cliente
                showMessage(mensagemEditarClienteDiv, '', '');
                try {
                    const response = await fetch(`/get_cliente/${id}`); // Nova rota
                    const cliente = await response.json();
                    if (response.ok) {
                        document.getElementById('id_editar_cliente').value = cliente.id;
                        document.getElementById('nome_editar_cliente').value = cliente.nome;
                        document.getElementById('data_aniversario_editar_cliente').value = cliente.data_aniversario;
                        editClienteModal.style.display = 'flex'; // Exibe o modal do cliente
                    } else {
                        showMessage(mensagemClienteDiv, cliente.message, 'error');
                    }
                } catch (error) {
                    console.error('Erro ao buscar cliente para edição:', error);
                    showMessage(mensagemClienteDiv, 'Erro ao carregar dados do cliente para edição.', 'error');
                }
            }
        }
        // --- Lógica de Exclusão ---
        else if (event.target.classList.contains('deletar-btn')) {
            const id = event.target.dataset.id;
            const type = event.target.dataset.type; // 'funcionario' ou 'cliente'
            const confirmacao = confirm(`Tem certeza que deseja excluir ${type === 'funcionario' ? 'este funcionário' : 'este cliente'}?`);

            if (confirmacao) {
                const url = type === 'funcionario' ? `/deletar_funcionario/${id}` : `/deletar_cliente/${id}`; // Novas rotas
                const mensagemDiv = type === 'funcionario' ? mensagemFuncionarioDiv : mensagemClienteDiv;

                try {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    const result = await response.json();

                    if (response.ok) {
                        showMessage(mensagemDiv, result.message, 'success');
                        await carregarTabelas(); // Carrega ambas as tabelas
                    } else {
                        showMessage(mensagemDiv, result.message, 'error');
                    }
                } catch (error) {
                    console.error(`Erro ao deletar ${type}:`, error);
                    showMessage(mensagemDiv, `Erro de comunicação ao deletar ${type}.`, 'error');
                }
            }
        }
    });

    // --- Fechar Modal de Funcionário ---
    closeFuncionarioModalBtn.addEventListener('click', () => {
        editFuncionarioModal.style.display = 'none';
    });
    window.addEventListener('click', (event) => {
        if (event.target == editFuncionarioModal) {
            editFuncionarioModal.style.display = 'none';
        }
    });

    // --- NOVO: Fechar Modal de Cliente ---
    closeClienteModalBtn.addEventListener('click', () => {
        editClienteModal.style.display = 'none';
    });
    window.addEventListener('click', (event) => {
        if (event.target == editClienteModal) {
            editClienteModal.style.display = 'none';
        }
    });


    // --- Enviar Dados do Formulário de Edição de Funcionário ---
    editFuncionarioForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(editFuncionarioForm);
        showMessage(mensagemEditarFuncionarioDiv, '', '');

        try {
            const response = await fetch('/editar_funcionario', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                showMessage(mensagemEditarFuncionarioDiv, result.message, 'success');
                await carregarTabelas();
                setTimeout(() => { editFuncionarioModal.style.display = 'none'; }, 1500);
            } else {
                showMessage(mensagemEditarFuncionarioDiv, result.message, 'error');
            }
        } catch (error) {
            console.error('Erro ao editar funcionário:', error);
            showMessage(mensagemEditarFuncionarioDiv, 'Erro de comunicação com o servidor.', 'error');
        }
    });

    // --- NOVO: Enviar Dados do Formulário de Edição de Cliente ---
    editClienteForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(editClienteForm);
        showMessage(mensagemEditarClienteDiv, '', '');

        try {
            const response = await fetch('/editar_cliente', { // Nova rota
                method: 'POST',
                body: formData
            });
            const result = await response.json();

            if (response.ok) {
                showMessage(mensagemEditarClienteDiv, result.message, 'success');
                await carregarTabelas();
                setTimeout(() => { editClienteModal.style.display = 'none'; }, 1500);
            } else {
                showMessage(mensagemEditarClienteDiv, result.message, 'error');
            }
        } catch (error) {
            console.error('Erro ao editar cliente:', error);
            showMessage(mensagemEditarClienteDiv, 'Erro de comunicação com o servidor.', 'error');
        }
    });


    // --- Função para Recarregar Ambas as Tabelas ---
    async function carregarTabelas() { // RENOMEADA
        try {
            const response = await fetch('/');
            const html = await response.text();

            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Atualiza a tabela de Funcionários
            const newFuncionariosTableBody = doc.querySelector('#funcionariosTable tbody');
            if (newFuncionariosTableBody) {
                funcionariosTableBody.innerHTML = newFuncionariosTableBody.innerHTML;
            } else {
                console.error("Não foi possível encontrar o tbody da tabela de funcionários na resposta.");
            }

            // NOVO: Atualiza a tabela de Clientes
            const newClientesTableBody = doc.querySelector('#clientesTable tbody');
            if (newClientesTableBody) {
                clientesTableBody.innerHTML = newClientesTableBody.innerHTML;
            } else {
                console.error("Não foi possível encontrar o tbody da tabela de clientes na resposta.");
            }

        } catch (error) {
            console.error('Erro ao carregar tabelas:', error);
            showMessage(mensagemFuncionarioDiv, 'Erro ao carregar a lista de pessoas.', 'error'); // Usa a mensagem de funcionário
        }
    }
});