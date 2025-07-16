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
                        method: 'POST', // Usamos POST para exclusão
                        headers: {
                            'Content-Type': 'application/json' // Pode enviar um corpo vazio, mas é bom especificar
                        },
                        body: JSON.stringify({}) // Corpo vazio ou { "id": funcionarioId }
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showMessage(mensagemDiv, result.message, 'success');
                        await carregarPessoas(); // Recarrega a lista para mostrar a remoção
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