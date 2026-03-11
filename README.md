# Robot Scenario Runner

Ferramenta desktop simples para executar runners Robot Framework através de uma interface gráfica.

Como funciona (V1 - manual):

- Esta versão remove a detecção automática de runners e argumentos.
- O usuário monta manualmente uma suite digitando até 5 keywords.
- Configure o caminho do repositório onde estão as automações Robot via `Configurações`.
- Clique em `Executar` para simular a execução e ver logs no console.

Estrutura do projeto:

- `app.py`: Ponto de entrada do aplicativo.
- `ui/`: Widgets da interface (janela principal, formulário dinâmico, console).
- `core/`: Lógica central (carregador de runners, parser de argumentos, executor robot, parser de resultados).
- `robot/runners/`: Local para armazenar runners Robot Framework (.robot).
- `output/logs/`: Local para saídas e logs de execução.

Requisitos:

- Python 3.11+
- Ver `requirements.txt`

Uso:

1. Abra a aplicação com `python app.py`.
2. Clique em `Configurações` e informe o caminho do repositório onde estão as automações.
3. Na tela principal digite uma `keyword` e clique em `Adicionar keyword` (máx 5).
4. Quando tiver ao menos uma keyword, clique em `Executar` para ver a simulação.

Observações:


- Limite de 5 keywords na suite.
- As keywords adicionadas aparecem na lista "Suite montada".
- A execução atual é simulada: os logs exibem a sequência de execução, sem chamar o Robot Framework.


