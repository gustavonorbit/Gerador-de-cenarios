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

Comportamento de execução:

- Se a suite contiver `keywords`, a ferramenta cria uma suite temporária que inclui os `Resource` detectados automaticamente (arquivos onde as keywords estão definidas) e executa-a com `python -m robot` usando a raiz da automação como `working directory`.
- Se a suite contiver `tests`, a ferramenta executa os testes por arquivo agrupando múltiplos `--test` por arquivo quando aplicável.
- Logs de indexação e execução aparecem no painel de console da aplicação; erros não quebram a UI.

Observações:

- A aplicação salva a última `raiz da automação` selecionada em `config.json` na pasta da ferramenta.
- Se o caminho salvo não existir ao iniciar a aplicação, será solicitado ao usuário selecionar uma nova pasta.
- Limites e heurísticas de indexação podem ser ajustados em `core/keyword_finder.py`.

