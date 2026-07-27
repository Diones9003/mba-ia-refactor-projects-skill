# Relatório de Auditoria — code-smells-project

## Cabeçalho
- **Projeto:** `code-smells-project` (API da Loja)
- **Stack:** Python 3 / Flask 3.1.1 (+ flask-cors 5.0.1) / SQLite (`sqlite3`, acesso manual via cursor)
- **Arquivos analisados:** `app.py`, `controllers.py`, `models.py`, `database.py`, `requirements.txt`
- **Linhas de código:** ~780 (app.py 88, controllers.py 292, models.py 314, database.py 86)
- **Domínio:** E-commerce — catálogo de produtos, usuários, pedidos/itens e relatório de vendas
- **Data da auditoria:** 2026-07-27

## Summary (contagem por severidade)
| Severidade | Quantidade |
|------------|------------|
| CRITICAL   | 5          |
| HIGH       | 5          |
| MEDIUM     | 5          |
| LOW        | 3          |
| **TOTAL**  | **18**     |

## Findings
> Ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW).

### [CRITICAL] SQL Injection por concatenação de strings
- **File:** `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:68`, `models.py:92`, `models.py:109-111`, `models.py:126-129`, `models.py:140`, `models.py:148-166`, `models.py:174`, `models.py:188`, `models.py:192`, `models.py:279-281`, `models.py:289-299`
- **Description:** Praticamente todas as queries do projeto são montadas concatenando strings com valores vindos do request. Exemplos: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` (28), o login `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (109-111) e a busca dinâmica que interpola `termo`/`categoria` diretamente no `LIKE` (289-297). Nenhuma dessas chamadas usa placeholders — apenas o seed em `database.py:70-83` é parametrizado.
- **Impact:** Injeção de SQL trivial. Um payload como `' OR '1'='1' --` no campo `email` do `/login` autentica sem senha; em `POST /produtos` o campo `nome` permite encerrar a instrução e executar comandos arbitrários. Leitura, alteração e destruição de qualquer dado.
- **Recommendation:** Converter **todas** as queries para parametrizadas (`?` placeholders), inclusive a query dinâmica de busca (montar a cláusula `WHERE` com placeholders e uma lista de parâmetros). Encapsular o acesso a dados em Models/Repositories que nunca aceitem SQL cru. Ver playbook padrão 4.

### [CRITICAL] Endpoint de execução de SQL arbitrário e reset de banco sem autenticação
- **File:** `app.py:59-78` (`/admin/query`), `app.py:47-57` (`/admin/reset-db`)
- **Description:** `POST /admin/query` executa qualquer SQL recebido no corpo da requisição (`cursor.execute(query)`, linha 69) e devolve o resultado; `POST /admin/reset-db` apaga todas as quatro tabelas. Nenhum dos dois exige autenticação, token ou qualquer verificação de origem.
- **Impact:** Equivalente a acesso administrativo irrestrito ao banco para qualquer cliente da rede — exfiltração total (incluindo senhas), alteração de preços/pedidos e destruição de todos os dados com uma única chamada.
- **Recommendation:** Remover ambos os endpoints do código de aplicação. Se um reset for necessário para desenvolvimento, expor apenas como script CLI ou condicionado a `FLASK_ENV=development` **e** protegido por autenticação. Nunca aceitar SQL cru do cliente.

### [CRITICAL] Senhas em texto puro — armazenadas, seedadas e expostas na API
- **File:** `models.py:126-129` (`criar_usuario`), `models.py:79-86` (`get_todos_usuarios` retorna `senha`), `models.py:95-102` (`get_usuario_por_id` retorna `senha`), `models.py:109-111` (comparação de senha em SQL), `database.py:75-79` (seed)
- **Description:** Senhas são gravadas sem hash, comparadas diretamente na cláusula `WHERE` do login e **serializadas na resposta** de `GET /usuarios` e `GET /usuarios/<id>` — ambos endpoints públicos, sem autenticação. O seed cria credenciais fracas em claro (`admin@loja.com` / `admin123`).
- **Impact:** `curl http://host/usuarios` devolve o dump completo de e-mails e senhas de todos os usuários, incluindo o admin. Comprometimento total de contas, agravado pelo reuso de senhas entre serviços.
- **Recommendation:** Aplicar hash forte (`bcrypt`/`argon2`) na criação e verificar via `check_password_hash` no login — nunca comparar senha em SQL. Remover o campo `senha` de toda serialização (serializer explícito no Model/View) e proteger os endpoints de usuários com autenticação.

### [CRITICAL] Hardcoded Secret / SECRET_KEY exposta no `/health`
- **File:** `app.py:7`, `controllers.py:285-289`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` está fixa no código-fonte versionado (app.py:7) e o endpoint público `/health` devolve a própria chave no JSON, junto com `db_path`, `debug` e `ambiente` (controllers.py:285-289).
- **Impact:** Segredo versionado no Git (impossível rotacionar sem alterar código) e publicamente legível via API — permite forjar sessões/assinaturas. O health check também vaza detalhes de infraestrutura úteis a um atacante.
- **Recommendation:** Mover para `.env` lido com `os.getenv("SECRET_KEY")`, adicionar `.env.example` e garantir `.env` no `.gitignore`. Reduzir o payload de `/health` a `status` + conectividade do banco. Ver playbook padrão 3.

### [CRITICAL] God Method / God File — `criar_pedido` e `controllers.py`
- **File:** `models.py:133-169` (`criar_pedido`), `controllers.py:1-292` (módulo inteiro), `models.py:1-314` (módulo inteiro)
- **Description:** `models.criar_pedido` concentra, numa única função: validação de existência de produto, validação de estoque, cálculo do total, inserção do pedido, inserção dos itens, baixa de estoque e controle de commit — além de devolver erros de negócio como dicionário `{"erro": ...}` (linhas 143/145), misturando fluxo de dados com contrato de resposta. Nos arquivos, `controllers.py` (292 linhas, 15 handlers) e `models.py` (314 linhas, 15 funções DAO) agrupam três domínios distintos (produtos, usuários, pedidos) sem qualquer separação.
- **Impact:** Impossível testar as regras de pedido em isolamento; qualquer alteração em estoque ou precificação toca a mesma função. A ausência de fronteiras por domínio faz com que cada mudança exija ler arquivos inteiros, e conflitos de merge são garantidos em times.
- **Recommendation:** Quebrar por domínio (`product`, `user`, `order`) e por camada: Controller (fluxo HTTP), Service (regra de negócio — cálculo de total, reserva de estoque), Model/Repository (persistência parametrizada). Substituir o retorno `{"erro": ...}` por exceções de domínio tratadas no error handler. Ver playbook padrões 1 e 2.

### [HIGH] Lógica de negócio e side-effects no Controller
- **File:** `controllers.py:208-210` (`criar_pedido`), `controllers.py:247-250` (`atualizar_status_pedido`)
- **Description:** O controller de pedido dispara "envio" de e-mail, SMS e push via `print(...)` (208-210) e o de status decide notificações e devolução de estoque inline, com `if novo_status == "aprovado"` / `"cancelado"` (247-250). São regras de negócio e integrações dentro do handler HTTP.
- **Impact:** As notificações só acontecem se o fluxo passar pelo HTTP — nenhum outro caminho (job, CLI, outro endpoint) as dispara. Regra não reutilizável nem testável, e o comentário "Devolver estoque" descreve um efeito que **não é implementado**, mascarando um bug real de inventário.
- **Recommendation:** Extrair um `NotificationService` e mover a transição de status para um `OrderService` que trate estoque e notificações como parte da regra. O controller apenas orquestra request → service → response. Ver playbook padrão 2.

### [HIGH] SQL dentro de loop (N+1 queries)
- **File:** `models.py:171-201` (`get_pedidos_usuario`), `models.py:203-233` (`get_todos_pedidos`)
- **Description:** Para cada pedido é executada uma query de itens (`cursor2`, linhas 188/220) e, para **cada item**, outra query de nome do produto (`cursor3`, linhas 192/224). Um `GET /pedidos` com 100 pedidos de 5 itens dispara 1 + 100 + 500 = 601 queries. Cada iteração ainda cria um novo cursor.
- **Impact:** Latência cresce com pedidos×itens; o endpoint se torna inutilizável com volume real e monopoliza a conexão única e global do processo.
- **Recommendation:** Uma única query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, agrupando os itens em memória por `pedido_id`. Ver playbook padrão 6.

### [HIGH] Acoplamento forte sem Injeção de Dependência — conexão global mutável
- **File:** `database.py:4-11` (globais `db_connection` / `db_path`), e as 15 funções de `models.py` que chamam `get_db()` internamente
- **Description:** A conexão é um singleton de módulo (`db_connection = None` + `global`), criada com `check_same_thread=False`, e o schema/seed são criados como efeito colateral do primeiro `get_db()` (database.py:14-84). Nenhuma função recebe a conexão como parâmetro — toda a camada de dados depende de estado global.
- **Impact:** Impossível testar com banco em memória ou mock sem monkeypatch global; impossível trocar SQLite por outro banco sem reescrever `models.py`. `check_same_thread=False` com uma única conexão compartilhada entre threads do Flask gera corrupção de estado transacional sob concorrência (ver finding de transação abaixo).
- **Recommendation:** Injetar a conexão/repositório via construtor ou parâmetro, gerenciar o ciclo de vida por request (`flask.g` + `teardown_appcontext`) e separar a criação de schema/seed num módulo de migração explícito, fora do caminho de leitura. Ver playbook padrão 9.

### [HIGH] Escritas multi-tabela sem transação explícita nem rollback
- **File:** `models.py:133-169` (`criar_pedido`), `app.py:47-57` (`/admin/reset-db`)
- **Description:** `criar_pedido` executa `INSERT` no pedido, `INSERT` de cada item e `UPDATE` de estoque acumulando tudo na transação implícita, com um único `db.commit()` no fim (linha 168) e **nenhum `try/except` com `rollback()`**. Se um item falhar no meio (produto removido em paralelo, erro de tipo), a exceção sobe para o controller sem desfazer nada — e como a conexão é global e compartilhada, as escritas pendentes ficam na transação e podem ser confirmadas por um `commit()` de uma **requisição posterior não relacionada**.
- **Impact:** Pedidos parcialmente gravados e baixa de estoque sem pedido correspondente — corrupção silenciosa de inventário e de faturamento, difícil de diagnosticar porque o commit acontece noutro request.
- **Recommendation:** Envolver a operação num bloco transacional explícito (`with connection:` ou `try/commit/except/rollback`) e garantir uma conexão por request. Combinar com a validação de estoque na mesma transação para evitar corrida.

### [HIGH] Violação de camadas — acesso direto ao banco em `app.py` e `controllers.py`
- **File:** `app.py:49-55`, `app.py:66-76`, `controllers.py:266-274` (`health_check`)
- **Description:** O arquivo de entrada abre cursores e executa SQL diretamente nas rotas administrativas, e `health_check` roda quatro queries de contagem (`SELECT COUNT(*) FROM ...`) dentro do controller, importando `get_db` (controllers.py:3). A camada de dados é atravessada.
- **Impact:** Nenhum ponto único controla o acesso ao banco — correções de segurança ou de conexão precisam ser replicadas em três arquivos; o roteamento fica impossível de testar sem banco.
- **Recommendation:** Todo acesso a dados passa pelos Models/Repositories; `app.py` só registra rotas e middlewares; `health_check` chama um método de repositório (`health.counts()`). Ver `04-mvc-guidelines.md`.

### [MEDIUM] Validação ausente, sem checagem de tipos e inconsistente entre endpoints
- **File:** `controllers.py:37-50` (`criar_produto`), `controllers.py:237-245` (`atualizar_status_pedido`), `controllers.py:153-158` (`criar_usuario`), `controllers.py:113-121` (`buscar_produtos`), `controllers.py:195-201` (`criar_pedido`)
- **Description:** As validações checam presença mas não tipo: `preco < 0` com `preco` recebido como string (`"10"`) levanta `TypeError` e retorna 500 em vez de 400 (controllers.py:43). `atualizar_status_pedido` valida o status mas nunca verifica se o pedido existe — atualizar um `pedido_id` inexistente responde `200 {"sucesso": true}`. `criar_usuario` aceita qualquer string como e-mail e não verifica duplicidade (a tabela não tem `UNIQUE`). `criar_pedido` não valida a estrutura dos itens, então um item sem `quantidade` estoura `KeyError` → 500. `float()` em `preco_min`/`preco_max` sem tratamento devolve 500 para query string inválida.
- **Impact:** Erros 500 evitáveis mascarando erros do cliente, dados corrompidos (usuários duplicados, e-mails inválidos) e falsos positivos de sucesso em operações que não fizeram nada.
- **Recommendation:** Camada de validação declarativa (schema/middleware) aplicada antes do controller, validando tipo, faixa e formato, e retornando 400 estruturado. Verificar existência do recurso antes de qualquer `UPDATE`. Ver playbook padrão 7.

### [MEDIUM] Duplicação de validação entre criar e atualizar produto
- **File:** `controllers.py:28-54` (`criar_produto`) vs. `controllers.py:72-90` (`atualizar_produto`)
- **Description:** Os dois handlers repetem quase o mesmo bloco: presença de `nome`/`preco`/`estoque`, `preco < 0`, `estoque < 0`. A divergência já começou — `atualizar_produto` **perdeu** as validações de tamanho de nome (47-50) e de categoria válida (52-54), presentes apenas em `criar_produto`.
- **Impact:** Prova concreta do custo da duplicação: é possível criar um produto com categoria válida e depois atualizá-lo para uma categoria inválida ou nome de 1 caractere, contornando as regras.
- **Recommendation:** Extrair um único validador de payload de produto, reutilizado por ambos os endpoints. Ver playbook padrões 5 e 7.

### [MEDIUM] Duplicação de serialização e de montagem de agregados
- **File:** `models.py:12-21`, `models.py:31-40`, `models.py:304-313` (serialização de produto ×3); `models.py:79-86`, `models.py:95-102` (usuário ×2); `models.py:178-200` vs. `models.py:211-232` (montagem de pedido+itens, corpos idênticos)
- **Description:** O mapeamento `row → dict` de produto é escrito literalmente três vezes com os mesmos oito campos; `get_todos_pedidos` e `get_pedidos_usuario` diferem **apenas** na cláusula `WHERE` e repetem ~20 linhas idênticas de montagem de itens.
- **Impact:** Adicionar uma coluna ou esconder um campo exige editar de 2 a 3 blocos; a divergência já ocorre em usuário (`login_usuario` omite `senha`, os outros dois expõem).
- **Recommendation:** Um serializer único por entidade (`to_dict`) na camada Model/View e uma função de montagem parametrizada pelo filtro. Ver playbook padrões 1 e 5.

### [MEDIUM] Magic Numbers e Magic Strings
- **File:** `models.py:256-262` (faixas de desconto), `controllers.py:52` (categorias válidas), `controllers.py:242` (status válidos), `database.py:5` (`db_path`), `app.py:88` (host/porta)
- **Description:** As faixas de desconto usam literais sem nome (`> 10000 → 0.1`, `> 5000 → 0.05`, `> 1000 → 0.02`); a lista de categorias válidas está embutida numa linha do controller e a de status de pedido em outra — ambas sem relação com o schema do banco, que aceita qualquer texto.
- **Impact:** A regra de negócio de desconto é ilegível e só existe no corpo de uma função de relatório; as listas de domínio podem divergir entre endpoints (nada impede o `/admin/query` ou o seed de gravar um status fora da lista).
- **Recommendation:** Extrair para constantes nomeadas / configuração (`DISCOUNT_TIERS`, `VALID_CATEGORIES`, `ORDER_STATUSES`) num módulo de domínio, referenciadas por validadores e services. Ver playbook padrão 8.

### [MEDIUM] CORS liberado para qualquer origem
- **File:** `app.py:9`
- **Description:** `CORS(app)` sem argumentos habilita `Access-Control-Allow-Origin: *` em todos os endpoints, incluindo `/login`, `/usuarios` (que devolve senhas) e as rotas `/admin/*`.
- **Impact:** Qualquer página web pode chamar a API a partir do navegador da vítima e ler a resposta — amplifica todos os findings de autenticação ausente para um vetor de ataque via browser.
- **Recommendation:** Restringir origens explicitamente via configuração (`CORS(app, origins=os.getenv("ALLOWED_ORIGINS").split(","))`), por ambiente. Ver playbook padrão 8.

### [LOW] `DEBUG=True` e bind em `0.0.0.0` fixos no código
- **File:** `app.py:8`, `app.py:88`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` — configuração insegura embutida, sem controle por ambiente.
- **Impact:** Werkzeug debugger acessível (execução de código via console PIN) e stack traces com trechos de código vazando para o cliente, em qualquer ambiente onde o processo rodar.
- **Recommendation:** Ler `DEBUG`, `HOST` e `PORT` de variáveis de ambiente com default seguro (`DEBUG=False`) e servir via WSGI em produção. Ver playbook padrão 8.

### [LOW] `print` como logging, com vazamento de dados sensíveis
- **File:** `controllers.py:8`, `controllers.py:11`, `controllers.py:57`, `controllers.py:61`, `controllers.py:106`, `controllers.py:161`, `controllers.py:179`, `controllers.py:182`, `controllers.py:208-210`, `controllers.py:219`, `controllers.py:248-250`, `app.py:56`, `app.py:83-86`
- **Description:** 15+ chamadas de `print` fazem o papel de log, com concatenação manual (`"ERRO: " + str(e)`), sem níveis, timestamp ou destino configurável. Entre elas, `print("Login bem-sucedido: " + email)` (179) e `print("Login falhou: " + email)` (182) registram e-mails de tentativas de autenticação em stdout.
- **Impact:** Impossível filtrar ou rotear logs por severidade; dados pessoais em stdout sem controle de retenção; mensagens de exceção cruas (`str(e)`) também retornam ao cliente nos `jsonify({"erro": str(e)})`, expondo detalhes internos do SQL.
- **Recommendation:** Substituir por `logging` com níveis e formatação estruturada, sem PII; no error handler centralizado, logar o detalhe e devolver ao cliente uma mensagem genérica.

### [LOW] Mensagens enganosas e nomenclatura que sombreia builtins
- **File:** `controllers.py:286-288` (`"ambiente": "producao"`), `controllers.py:249-250` ("Devolver estoque"), `controllers.py:14`/`64`/`98` (parâmetro `id`), `controllers.py:113` (`termo` derivado de `q`)
- **Description:** `/health` afirma `"ambiente": "producao"` num app com SQLite local e `DEBUG=True`; a notificação de cancelamento anuncia "Devolver estoque" numa operação que não devolve estoque nenhum. Os handlers de produto usam `id` como nome de parâmetro, sombreando o builtin, e `criar_produto` reatribui `id` ao resultado do model (linha 56).
- **Impact:** Mensagens que mentem sobre o comportamento mascaram dívida técnica e bugs reais (o estoque não devolvido); o shadowing de `id` prejudica leitura e ferramentas de análise.
- **Recommendation:** Derivar `ambiente` da configuração real, remover mensagens que descrevem efeitos não implementados (ou implementá-los) e renomear parâmetros para `produto_id`/`usuario_id`.

## Rodapé
- **Total de findings:** 18
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
