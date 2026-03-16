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
4. Quando tiver ao menos uma keyword, clique em `Executar` para gerar uma suite temporária e executá-la com o Robot Framework.

Observações:


- Limite de 5 keywords na suite.
- As keywords adicionadas aparecem na lista "Suite montada".
 - A execução gera uma suite temporária (.robot) com as keywords adicionadas (até 5) e a executa de fato com o Robot Framework.
 - A execução é realizada com o comando `python -m robot` e não gera `output`, `log` nem `report` (usamos `--output NONE --log NONE --report NONE`).
 - A opção "Mostrar tela da automação" envia a variável Robot `SHOW_UI` como `True`/`False` para a suite; suas automações podem usar essa variável para controlar headless/visible.
 - A execução ocorre com o diretório de trabalho configurado como o repositório informado em `Configurações`, garantindo que recursos relativos sejam acessíveis.
 - A execução gera uma suite temporária (.robot) com as keywords adicionadas (até 5) e a executa de fato com o Robot Framework.
 - Você pode configurar um `Resource base do Robot` nas Configurações. Se informado, a suite temporária incluirá este resource para que as keywords definidas no seu projeto sejam encontradas.
 - O `Resource base` pode ser um caminho absoluto ou relativo ao `repository_path`. Se o arquivo não existir, a execução será bloqueada e o erro exibido no console.
 - A execução é realizada com o comando `python -m robot` e não gera `output`, `log` nem `report` (usamos `--output NONE --log NONE --report NONE`).
 - A opção "Mostrar tela da automação" envia a variável Robot `SHOW_UI` como `True`/`False` para a suite; suas automações podem usar essa variável para controlar headless/visible.
 - A execução ocorre com o diretório de trabalho configurado como o repositório informado em `Configurações`, garantindo que recursos relativos sejam acessíveis.


