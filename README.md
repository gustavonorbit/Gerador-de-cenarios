
# Robot Scenario Runner

Ferramenta desktop para montar e executar suites Robot Framework com experiência simplificada
e pronta para uso real.

Principais mudanças na arquitetura:

- A raiz do projeto é detectada automaticamente: é a pasta onde a aplicação está localizada/executada.
- Não há mais seleção manual de `repository_path` ou `base_resource_path` — tudo é resolvido automaticamente.
- Ao abrir a aplicação, os arquivos `*.robot` e `*.resource` são indexados automaticamente (ignorando `.git`, `venv`, `__pycache__`, `node_modules`, etc.).
- O usuário apenas começa a digitar keywords; a ferramenta sugere correspondências e monta a suite automaticamente.
- A execução usa a raiz do projeto como `working directory`.

Estrutura do projeto (resumido):

- `app.py`: ponto de entrada.
- `ui/`: interface gráfica (janela principal, console, tela de execução).
- `core/`: lógica de indexação, geração de suites e execução Robot.

Requisitos:

- Python 3.11+
- Ver `requirements.txt`

Uso:

1. Coloque esta ferramenta dentro da raiz do seu projeto de automação Robot (a mesma pasta que contém suas pastas `robot/`, `tests_robot/`, etc.) ou execute-a a partir dessa pasta.
2. Abra a aplicação com `python app.py`.
3. A aplicação irá detectar automaticamente a raiz do projeto e indexar os arquivos Robot.
4. Comece a digitar keywords no campo de busca — sugestões aparecerão automaticamente.
5. Adicione até 5 keywords à suite montada e clique em `Executar`.

Comportamento de execução:

- A ferramenta localiza automaticamente em quais arquivos as keywords estão definidas e inclui os `Resource` correspondentes na suite temporária.
- A suite temporária é gerada e executada com `python -m robot` usando a raiz do projeto como diretório de trabalho.
- Logs são exibidos no painel de console da aplicação (erros de indexação/execução não quebram a UI).

Observações:

- Limite de 5 keywords por execução.
- Se ocorrerem erros durante a indexação, a aplicação os reportará no console e continuará funcional.
- Não é mais necessário configurar manualmente caminhos para resources ou repositório.


