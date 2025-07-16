// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const registroForm = document.getElementById('registroForm');
    const mensagemDiv = document.getElementById('mensagem');
    const pessoasTableBody = document.querySelector('#pessoasTable tbody');

    // Elementos do Modal de Edição
    const editModal = document.getElementById('editModal');
    const closeButton = document.querySelector('.close-button');
    const editForm = document.getElementById('editForm');
    const mensagemEditarDiv = document.getElementById('mensagem_editar');

    // Campos de Data do Formulário de Registro
    const entryAdmissao = document.getElementById('data_admissao');
    const entryAniversario = document.getElementById('data_aniversario');
    const entryLicenca = document.getElementById('data_retorno_licenca');

    // Campos de Data do Formulário de Edição
    const entryAdmissaoEditar = document.getElementById('data_admissao_editar');
    const entryAniversarioEditar = document.getElementById('data_aniversario_editar');
    const entryLicencaEditar = document.getElementById('data_retorno_licenca_editar');

    // --- Função para formatar a data automaticamente (DD/MM/AAAA) ---
    function formatarData(event) {
        let input = event.target;
        let value = input.value.replace(/\D/g, ''); // Remove tudo que não for dígito

        // Se o evento for de backspace, não adiciona barras automaticamente para não atrapalhar
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
    entryAdmissao.addEventListener('input', formatarData);
    entryAniversario.addEventListener('input', formatarData);
    entryLicenca.addEventListener('input', formatarData);

    entryAdmissaoEditar.addEventListener('input', formatarData);
    entryAniversarioEditar.addEventListener('input', formatarData);
    entryLicencaEditar.addEventListener('input', formatarData);


    // Função para exibir mensagem
    function showMessage(divElement, message, type) {
        divElement.textContent = message;
        divElement.classList.remove('success', 'error');
        if (type) {
            divElement.classList.add(type);
        }
    }

    // --- Lógica de Registro ---
    registroForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(registroForm);
        showMessage(mensagemDiv, '', '');

        try {
            const response = await fetch('/adicionar_funcionario', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(mensagemDiv, result.message, 'success');
                registroForm.reset();
                await carregarPessoas();
            } else {
                showMessage(mensagemDiv, result.message, 'error');
            }
        } catch (error) {
            console.error('Erro:', error);
            showMessage(mensagemDiv, 'Erro de comunicação com o servidor.', 'error');
        }
    });

    // --- Lógica de Edição ---

    // Abre o modal de edição ao clicar no botão "Editar"
    pessoasTableBody.addEventListener('click', async (event) => {
        if (event.target.classList.contains('editar-btn')) {
            const funcionarioId = event.target.dataset.id;
            showMessage(mensagemEditarDiv, '', '');

            try {
                const response = await fetch(`/get_funcionario/${funcionarioId}`);
                const funcionario = await response.json();

                if (response.ok) {
                    document.getElementById('id_editar').value = funcionario.id;
                    document.getElementById('nome_editar').value = funcionario.nome;
                    document.getElementById('data_admissao_editar').value = funcionario.data_admissao;
                    document.getElementById('data_aniversario_editar').value = funcionario.data_aniversario;
                    document.getElementById('data_retorno_licenca_editar').value = funcionario.data_retorno_licenca || '';

                    editModal.style.display = 'flex';
                } else {
                    showMessage(mensagemDiv, funcionario.message, 'error');
                }
            } catch (error) {
                console.error('Erro ao buscar funcionário para edição:', error);
                showMessage(mensagemDiv, 'Erro ao carregar dados para edição.', 'error');
            }
        }
        // --- Lógica de Exclusão (adicionada aqui) ---
        else if (event.target.classList.contains('deletar-btn')) {
            const funcionarioId = event.target.dataset.id;
            const confirmacao = confirm("Tem certeza que deseja excluir esta pessoa?");

            if (confirmacao) {
                try {
                    const response = await fetch(`/deletar_funcionario/${funcionarioId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({})
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showMessage(mensagemDiv, result.message, 'success');
                        await carregarPessoas();
                    } else {
                        showMessage(mensagemDiv, result.message, 'error');
                    }
                } catch (error) {
                    console.error('Erro ao deletar funcionário:', error);
                    showMessage(mensagemDiv, 'Erro de comunicação ao deletar.', 'error');
                }
            }
        }
    });


    // Fecha o modal ao clicar no botão de fechar ou fora do conteúdo
    closeButton.addEventListener('click', () => {
        editModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target == editModal) {
            editModal.style.display = 'none';
        }
    });

    // Envia os dados do formulário de edição
    editForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(editForm);
        showMessage(mensagemEditarDiv, '', '');

        try {
            const response = await fetch('/editar_funcionario', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(mensagemEditarDiv, result.message, 'success');
                await carregarPessoas();
                setTimeout(() => {
                    editModal.style.display = 'none';
                }, 1500);
            } else {
                showMessage(mensagemEditarDiv, result.message, 'error');
            }
        } catch (error) {
            console.error('Erro ao editar:', error);
            showMessage(mensagemEditarDiv, 'Erro de comunicação com o servidor.', 'error');
        }
    });

    // --- Função para Recarregar a Tabela ---
    async function carregarPessoas() {
        try {
            const response = await fetch('/');
            const html = await response.text();

            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            const newTableBody = doc.querySelector('#pessoasTable tbody');
            if (newTableBody) {
                pessoasTableBody.innerHTML = newTableBody.innerHTML;
            } else {
                console.error("Não foi possível encontrar o tbody na resposta da requisição.");
            }
        } catch (error) {
            console.error('Erro ao carregar pessoas:', error);
            showMessage(mensagemDiv, 'Erro ao carregar a lista de pessoas.', 'error');
        }
    }
});