# Robot Scenario Runner

Ferramenta desktop para montar e executar suites Robot Framework com experiência simples e pronta para uso.

Resumo da nova arquitetura:

- O usuário seleciona a `raiz da automação` (pasta do projeto Robot) via um botão na UI.
- A pasta selecionada é salva automaticamente e reutilizada na próxima vez que a aplicação for aberta (se ainda existir).
- A aplicação indexa recursivamente `*.robot` e `*.resource` dentro da raiz selecionada, ignorando diretórios comuns como `.git`, `venv`, `__pycache__`, `node_modules`, `dist`, `build`, `.idea`, `.vscode`.
- A busca unificada sugere `keywords` e `tests` encontrados no índice.
- A execução utiliza o `working directory` igual à raiz da automação selecionada.

Principais componentes:

- `app.py`: ponto de entrada.
- `ui/main_window.py`: interface principal — seleção de raiz, busca, sugestões, montagem da suite e execução.
- `core/keyword_finder.py`: indexador que mapeia keywords e testes para os arquivos onde estão definidos.
- `core/suite_builder.py`: gera suites temporárias para execução de keywords (inclui automa­ticamente os Resources detectados).
- `core/robot_executor.py`: executa Robot Framework (`python -m robot`) e encaminha logs para a UI.
- `core/config_manager.py`: armazena a `automation_root_path` em `config.json` na pasta da aplicação.

Requisitos:

- Python 3.11+
- Dependências listadas em `requirements.txt` (PySide6, Robot Framework, etc.)

Uso:

1. Execute a aplicação com:

```bash
python app.py
```

2. Na tela principal clique em `Selecionar raiz da automação` e escolha a pasta do seu projeto Robot.
3. A aplicação salvará esse caminho e indexará automaticamente os arquivos do projeto.
4. Comece a digitar no campo de busca; sugestões de `keywords` e `tests` aparecerão.
5. Adicione itens à suite montada e clique em `Executar`.

6. Antes de clicar em `Executar`, escolha a `Base de execução` no seletor disponível na tela principal. Opções suportadas:
	- `SQL` (padrão)
	- `SAP`
	- `ORACLE`

A variável selecionada será enviada ao Robot como `CURRENT_DB` (ex.: `-v CURRENT_DB:SQL`).

Comportamento de execução:

- Se a suite contiver `keywords`, a ferramenta cria uma suite temporária que inclui os `Resource` detectados automaticamente (arquivos onde as keywords estão definidas) e executa-a com `python -m robot` usando a raiz da automação como `working directory`.
- Se a suite contiver `tests`, a ferramenta executa os testes por arquivo agrupando múltiplos `--test` por arquivo quando aplicável.
- Logs de indexação e execução aparecem no painel de console da aplicação; erros não quebram a UI.

Observações:

- A aplicação salva a última `raiz da automação` selecionada em `config.json` na pasta da ferramenta.
- Se o caminho salvo não existir ao iniciar a aplicação, será solicitado ao usuário selecionar uma nova pasta.
- Limites e heurísticas de indexação podem ser ajustados em `core/keyword_finder.py`.

Modo de execução: Desktop vs Web
--------------------------------

- **Tipo de automação**: a interface agora permite escolher entre `Desktop` e `Web` antes de executar.

- **Desktop** (padrão): a UI exibirá o seletor `Base de execução` (CURRENT_DB). O valor selecionado será enviado ao Robot como variável `CURRENT_DB` (ex.: `-v CURRENT_DB:SQL`). O checkbox `Mostrar tela da automação (Web)` ficará oculto.

- **Web**: a UI exibirá o checkbox `Mostrar tela da automação (Web)` e ocultará o seletor `Base de execução`. Neste modo a ferramenta **não** envia `CURRENT_DB` ao Robot; em vez disso envia `SHOW_UI` (com valor `True` ou `False` conforme o checkbox). Esse modo prepara a interface para futuras parametrizações específicas de automação Web.

Logs úteis relacionados ao modo de execução são exibidos no painel de console ao iniciar a execução, por exemplo:

- `Tipo de automação selecionado: Desktop`
- `Base de execução selecionada: SQL`
ou
- `Tipo de automação selecionado: Web`
- `Mostrar tela da automação (Web): ativado`

Essa separação mantém o comportamento atual para automações Desktop, evita enviar parâmetros irrelevantes para Web e torna a UI mais clara para o usuário.

Cenários Salvos
---------------

Além de `Favoritos` (itens individuais), a aplicação suporta **Cenários Salvos** — uma suite montada que pode ser persistida e reutilizada.

- Para salvar a suite atual, use o botão `+` no cabeçalho `Suite montada` e forneça um nome.
- Cenários armazenam os itens na ordem atual, incluindo argumentos preenchidos.
- Abra `Cenários Salvos` pelo botão homônimo no topo para carregar, editar ou remover cenários.

Logs relacionados:
- `Cenário salvo: <nome>`
- `Cenário carregado: <nome>`
- `Cenário removido: <nome>`
- `Cenário atualizado: <nome>`

