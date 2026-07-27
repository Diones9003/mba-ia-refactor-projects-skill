# Relatório de Auditoria — task-manager-api

## Cabeçalho
- **Projeto:** `task-manager-api` (Task Manager API)
- **Stack:** Python 3 / Flask 3.0.0 (+ flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1) / SQLite via ORM SQLAlchemy (`sqlite:///tasks.db`)
- **Arquivos analisados:** `app.py`, `database.py`, `seed.py`, `models/{user,task,category}.py`, `routes/{task,user,report}_routes.py`, `services/notification_service.py`, `utils/helpers.py`
- **Linhas de código:** 1.158 (task_routes 299, report_routes 223, user_routes 211, helpers 116, seed 99, task 60, notification_service 48, user 38, app 34, category 21, database 3)
- **Domínio:** Gestão de tarefas — usuários, tarefas, categorias, relatórios de produtividade e notificações
- **Data da auditoria:** 2026-07-27
- **Endpoints mapeados:** 22 (7 tasks · 7 users/login · 6 reports/categories · 2 root)

> Projeto mais organizado que os demais do desafio: já possui pastas `models/`, `routes/`, `services/`, `utils/` (MVC parcial). Porém as pastas são **cosméticas** — `routes/` concentra validação, regra de negócio, acesso a dados e serialização; `services/` contém código morto; `utils/` contém validadores e constantes que **ninguém importa**. Não existe camada de controller, config ou middleware.

## Summary (contagem por severidade)
| Severidade | Quantidade |
|------------|------------|
| CRITICAL   | 4          |
| HIGH       | 5          |
| MEDIUM     | 6          |
| LOW        | 4          |
| **TOTAL**  | **19**     |

## Findings
> Ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW).

### [CRITICAL] C2 — Hardcoded Credentials / Secrets
- **File:** `app.py:11-13`, `services/notification_service.py:7-10`
- **Description:** `SECRET_KEY = 'super-secret-key-123'` fixa em `app.py:13`; URI do banco fixa em `app.py:11`; o `NotificationService` traz host, porta, usuário e **senha SMTP em claro** (`self.email_password = 'senha123'`, linha 10). O projeto declara `python-dotenv==1.0.0` no `requirements.txt` mas **não existe `.env` nem `.env.example`**, e nenhum `os.getenv` é chamado em todo o código.
- **Impact:** Credenciais versionadas em Git — histórico permanente, impossível rotacionar sem alterar código; com a `SECRET_KEY` conhecida qualquer sessão/token assinado pela app é forjável.
- **Recommendation:** Extrair tudo para `.env` + camada `src/config/` lendo via `os.getenv` com defaults seguros; criar `.env.example` versionado. Ver playbook padrão 3.

### [CRITICAL] Hash de senha com MD5 sem salt
- **File:** `models/user.py:27-32`
- **Description:** `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` (linha 29) e `check_password` compara MD5 diretamente (linha 32). MD5 é rápido, sem salt e sem fator de custo. Agravante: `user_routes.py:64` aceita senha com **mínimo de 4 caracteres**, e o `seed.py` cadastra senhas reais como `1234`, `abcd`, `pass`.
- **Impact:** Hashes MD5 sem salt são reversíveis por rainbow table em segundos; senhas de 4 caracteres caem por força bruta instantânea. Vazamento do banco = comprometimento de todas as contas, incluindo a de `role='admin'`.
- **Recommendation:** Migrar para `werkzeug.security.generate_password_hash`/`check_password_hash` (scrypt, já disponível via Flask) ou bcrypt/argon2 com salt por usuário; elevar o mínimo de senha para 8+. Ver catálogo — *APIs deprecated / hashing caseiro*.

### [CRITICAL] Hash de senha exposto nas respostas da API
- **File:** `models/user.py:16-25`, `routes/user_routes.py:33`, `routes/user_routes.py:85`, `routes/user_routes.py:209`
- **Description:** `User.to_dict()` inclui `'password': self.password` (linha 21). Esse dicionário é devolvido tal e qual por `GET /users/<id>` (`user_routes.py:33`), `POST /users` (linha 85) e `POST /login` (linha 209) — endpoints **sem qualquer autenticação**.
- **Impact:** Qualquer requisição anônima a `GET /users/1` devolve o hash MD5 do usuário. Combinado com o finding anterior, é caminho direto para tomada de conta administrativa — não é vazamento teórico, é o comportamento padrão da rota.
- **Recommendation:** Nunca serializar o campo `password`. Criar serializer explícito na camada View (`user_serializer.to_public_dict`) com whitelist de campos, e usá-lo em todas as respostas. Ver playbook padrão 5 e guidelines da camada View.

### [CRITICAL] Ausência total de autenticação/autorização e escalonamento de privilégio
- **File:** `routes/user_routes.py:185-211`, `routes/user_routes.py:52`, `routes/user_routes.py:119-122`, `routes/user_routes.py:134-151`
- **Description:** `POST /login` devolve `'token': 'fake-jwt-token-' + str(user.id)` (linha 210) — string previsível, não assinada, sem expiração — e **nenhuma rota valida token algum**. Não há decorator de auth em nenhum dos 22 endpoints. Além disso `POST /users` aceita `role` direto do corpo da requisição (linha 52, validado apenas contra a lista em 71-72), permitindo que qualquer anônimo crie um usuário `admin`. `User.is_admin()` (`models/user.py:34`) existe mas **nunca é chamado**. `DELETE /users/<id>` (linha 134) apaga usuário e todas as suas tasks sem autenticação.
- **Impact:** Falha estrutural de controle de acesso. Qualquer cliente na rede pode se autopromover a admin, ler todos os usuários, apagar dados de terceiros e alterar qualquer task. As roles no schema (`user`/`admin`/`manager`) são decorativas.
- **Recommendation:** Introduzir `src/middlewares/auth.py` com emissão/validação de JWT real (assinado com a `SECRET_KEY` do `.env`, com `exp`), decorators `@require_auth` e `@require_role('admin')` aplicados às rotas de escrita; remover `role` do payload público de criação. Ver playbook padrões 3 e 7.

### [HIGH] C1 — God File / God Method e responsabilidades misturadas
- **File:** `routes/task_routes.py:1-299`, `routes/report_routes.py:12-101`, `routes/report_routes.py:157-223`
- **Description:** `task_routes.py` tem 299 linhas e 7 handlers, cada um fazendo parsing de request + validação + regra de negócio + acesso a dados + serialização manual. `summary_report` (`report_routes.py:12-101`) é um God Method de 90 linhas que emite ~15 queries e monta um relatório de 6 seções. Pior: o CRUD completo de **categorias** (`report_routes.py:157-223`) mora no arquivo de *relatórios* — domínio errado, e por isso `GET /categories` e `POST /categories` estão registrados no `report_bp`.
- **Impact:** Impossível testar regra de negócio sem subir HTTP; qualquer alteração em "overdue" ou em estatísticas exige varrer três arquivos; a rota de categorias é impossível de localizar por convenção.
- **Recommendation:** Quebrar em Controller (fluxo) → Service (regra) → Model (dados); criar `category_routes`/`category_controller` próprios e um `report_service` que produza o dicionário do relatório. Ver playbook padrões 1 e 2.

### [HIGH] H1 — Lógica de negócio nas rotas e models anêmicos
- **File:** `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:281-297`, `routes/user_routes.py:140-142`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`, `routes/report_routes.py:119-151`
- **Description:** A regra "task atrasada" está reimplementada **quatro vezes** dentro de handlers HTTP (task_routes 30-39, 71-80, 283-287; user_routes 171-180; report_routes 33-37, 132-135) — enquanto `Task.is_overdue()` (`models/task.py:50`) existe e **nunca é chamado**. Idem `Task.validate_status` e `Task.validate_priority` (`models/task.py:38-48`): código morto, com as rotas repetindo a lista de status literal. `completion_rate` é calculado inline em três lugares (task_routes:296, report_routes:67, report_routes:151) apesar de `utils/helpers.calculate_percentage` existir. O cascade delete de tasks ao remover usuário é feito manualmente na rota (`user_routes.py:140-142`) em vez de ser uma regra do model/relacionamento.
- **Impact:** Uma correção na definição de "atrasada" precisa ser aplicada em 4 pontos, com divergência garantida; nada disso é testável sem cliente HTTP; o cascade manual não roda se a task for apagada por outro caminho.
- **Recommendation:** Mover a regra para `Task.is_overdue()` e para `TaskService`/`ReportService`; declarar `cascade='all, delete-orphan'` no relacionamento `User.tasks`; controller apenas orquestra. Ver playbook padrão 2.

### [HIGH] H2 — Acoplamento forte sem injeção de dependência nem application factory
- **File:** `app.py:9-31`, `database.py:1-3`, `services/notification_service.py:4-10`
- **Description:** `app`, `config` e o `db` são criados em nível de módulo (`app.py:9-16`), e `db.create_all()` roda **no import** (`app.py:30-31`) — ou seja, importar `app` cria arquivo de banco como efeito colateral (é o que `seed.py:2` faz). Não existe `create_app()`, então não há como instanciar a aplicação com configuração de teste. Todos os blueprints importam o singleton global `from database import db`. O `NotificationService` fixa suas dependências no `__init__` (linhas 7-10) e **nunca é instanciado em lugar algum** — os 48 linhas são código morto acoplado a `smtplib`.
- **Impact:** Testes exigem o banco real; trocar SQLite por Postgres ou stubbar o envio de e-mail obriga a editar as classes; import com efeito colateral torna a ordem de import significativa.
- **Recommendation:** `create_app(config_name)` como factory, config por objeto/classe em `src/config/`, `db.init_app(app)` dentro da factory, migração de schema fora do import, e `NotificationService` recebendo credenciais/transporte por construtor. Ver playbook padrão 9.

### [HIGH] H3 — SQL/consultas dentro de loop (N+1 queries)
- **File:** `routes/task_routes.py:41-57`, `routes/report_routes.py:53-68`, `routes/report_routes.py:157-165`, `routes/user_routes.py:22`, `routes/report_routes.py:19-28`
- **Description:** Em `GET /tasks`, cada task dispara `User.query.get` (linha 42) e `Category.query.get` (linha 51) — 2N+1 queries. Em `/reports/summary`, o laço `for u in users` executa `Task.query.filter_by(user_id=u.id).all()` por usuário (linha 56). Em `GET /categories`, cada categoria dispara um `Task.query.filter_by(...).count()` (linha 163). Em `GET /users`, `len(u.tasks)` (linha 22) força um lazy load por usuário. Ainda em `/reports/summary`, as contagens por status e prioridade são **9 queries `COUNT` separadas** (linhas 19-28) que caberiam em um único `GROUP BY`.
- **Impact:** Latência cresce linearmente com o volume: com 1.000 tasks, `GET /tasks` faz ~2.001 round-trips. O relatório degrada com o número de usuários e categorias simultaneamente.
- **Recommendation:** `joinedload`/`selectinload` para os relacionamentos de task; `func.count` + `group_by` para as agregações de status/prioridade; contagem de tasks por categoria e por usuário via `outerjoin` + `group_by`. Ver playbook padrão 6.

### [HIGH] Servidor de desenvolvimento exposto com debugger ativo
- **File:** `app.py:34`
- **Description:** `app.run(debug=True, host='0.0.0.0', port=5000)` — o debugger interativo do Werkzeug é servido em todas as interfaces de rede, e nenhuma variável de ambiente controla isso.
- **Impact:** Tracebacks com trechos de código e valores de variáveis são devolvidos a qualquer cliente em erro; o console do Werkzeug é um vetor conhecido de execução remota de código. Não há separação entre configuração de dev e de produção.
- **Recommendation:** `debug` e `host` vindos do `.env` (`FLASK_DEBUG=false` por padrão), servidor WSGI real em produção. Ver playbook padrão 3 e anti-pattern L2.

### [MEDIUM] M1 — Validação dispersa, divergente e propensa a 500
- **File:** `routes/task_routes.py:96-124`, `routes/task_routes.py:166-213`, `routes/user_routes.py:54-72`, `routes/user_routes.py:102-125`, `routes/report_routes.py:196-202`, `utils/helpers.py:57-108`
- **Description:** As mesmas regras (título 3-200, status na lista, prioridade 1-5, regex de e-mail, role na lista) são reescritas inline no `create` e novamente no `update` de cada recurso, com mensagens divergentes entre eles (`'Título muito curto'` vs. a mensagem do helper). Enquanto isso `helpers.process_task_data` (linhas 57-108) faz exatamente essa validação e **não é importado por ninguém**, e `marshmallow` está no `requirements.txt` sem uso. Pior, a validação é feita **sem checagem de tipo**, o que gera 500 em vez de 400: `task_routes.py:113` (`priority < 1` estoura `TypeError` se vier `"alta"`), `task_routes.py:167` (`len(data['title'])` estoura se `title` for `null` ou número), `task_routes.py:261/264` (`int(priority)` estoura `ValueError` com query string não numérica, sem `try`), e `report_routes.py:196` acessa `data['name']` sem o guard `if not data` que as outras rotas têm.
- **Impact:** Cliente recebe 500 opaco em erro de entrada trivial; contratos inconsistentes entre criar e atualizar; código de validação morto em `utils/`.
- **Recommendation:** Schemas marshmallow por recurso em `src/models/schemas/` (ou validadores dedicados), aplicados por decorator/middleware antes do controller, com erro 400 padronizado. Ver playbook padrão 7.

### [MEDIUM] M2 — Magic strings/numbers com constantes nomeadas mortas ao lado
- **File:** `utils/helpers.py:110-116`, `routes/task_routes.py:110`, `routes/task_routes.py:177`, `routes/user_routes.py:71`, `routes/user_routes.py:120`, `models/task.py:39`
- **Description:** `utils/helpers.py:110-116` define `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` — e **nenhuma delas é importada em qualquer arquivo**. Em paralelo, a lista literal `['pending', 'in_progress', 'done', 'cancelled']` aparece em `task_routes.py:110`, `:177` e `models/task.py:39`, a string `'pending'` aparece 19 vezes no projeto, `['user','admin','manager']` está duplicada em `user_routes.py:71` e `:120`, e os limites `3`/`200`/`1`/`5`/`4` estão espalhados como literais.
- **Impact:** Adicionar um status novo exige caçar literais em três arquivos; as constantes existentes dão falsa sensação de centralização.
- **Recommendation:** Consolidar em `src/config/constants.py` (ou enums), importar em models, schemas e services, e eliminar os literais. Ver playbook padrão 8.

### [MEDIUM] M3 — Duplicação de serialização e de cálculo de estatísticas
- **File:** `routes/task_routes.py:17-28`, `routes/user_routes.py:162-169`, `models/task.py:23-36`, `routes/task_routes.py:273-299`, `routes/report_routes.py:103-155`, `routes/user_routes.py:61`, `routes/user_routes.py:106`
- **Description:** A montagem do dicionário da task é feita campo a campo em `task_routes.py:17-28` e outra vez, com subconjunto diferente de campos, em `user_routes.py:162-169` — apesar de `Task.to_dict()` já existir (`models/task.py:23`) e ser usada em outras rotas: o mesmo recurso é serializado com três formatos distintos dependendo do endpoint. As estatísticas de task por status/atraso/completion_rate estão implementadas em `GET /tasks/stats` (task_routes:273-299) e novamente em `/reports/user/<id>` (report_routes:119-151) e em `/reports/summary`. O regex de e-mail está copiado em `user_routes.py:61` e `:106`, com `helpers.validate_email:21` idêntico e sem uso.
- **Impact:** Contrato de API incoerente para o mesmo recurso; correção de bug de serialização precisa ser feita em N lugares.
- **Recommendation:** Uma camada de serializers em `src/views/` como fonte única (com variações explícitas tipo `summary`/`detail`), e um `TaskStatsService` reutilizado pelos três endpoints. Ver playbook padrões 1 e 5.

### [MEDIUM] Error handling ausente: 12 `except:` nus e `print` como log
- **File:** `routes/task_routes.py:62`, `routes/task_routes.py:137`, `routes/task_routes.py:204`, `routes/task_routes.py:236`, `routes/user_routes.py:130`, `routes/user_routes.py:149`, `routes/report_routes.py:186`, `routes/report_routes.py:207`, `routes/report_routes.py:221`, `utils/helpers.py:46`, `utils/helpers.py:49`, `utils/helpers.py:88`
- **Description:** 12 blocos `except:` nus (bare except) capturam qualquer coisa — inclusive `KeyboardInterrupt` e `SystemExit` — e devolvem 500 genérico sem registrar a causa; o caso mais grave é `get_tasks` (`task_routes.py:62-63`), que engole toda falha da rota mais movimentada. Onde há log, é `print()` em stdout (14 ocorrências em `routes/`, `services/`, `utils/`), sem nível, timestamp ou correlação — e `helpers.log_action:36` "loga" com `print`. Não existe error handler registrado no Flask, então erros fora dos `try` retornam HTML de traceback.
- **Impact:** Falhas reais ficam invisíveis em produção; diagnóstico exige reproduzir localmente; respostas de erro não padronizadas.
- **Recommendation:** `src/middlewares/error_handler.py` com `@app.errorhandler` para `HTTPException`, exceções de domínio e `Exception`, resposta JSON padronizada, e `logging` estruturado substituindo todos os `print`. Ver playbook padrão 5.

### [MEDIUM] APIs deprecated — `Query.get()` (16×) e `datetime.utcnow()` (18×)
- **File:** `routes/task_routes.py` (9 ocorrências de `.query.get`), `routes/user_routes.py` (4), `routes/report_routes.py` (3); `datetime.utcnow()` em `models/task.py`, `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`, `services/notification_service.py`, `utils/helpers.py`, `seed.py`
- **Description:** `Model.query.get(id)` está deprecado no SQLAlchemy 2.x (a app usa flask-sqlalchemy 3.1.1, que já roda no core 2.x) em favor de `db.session.get(Model, id)` — 16 chamadas. `datetime.utcnow()` está deprecado a partir do Python 3.12 em favor de `datetime.now(timezone.utc)` — 18 chamadas, incluindo os `default=datetime.utcnow` das colunas.
- **Impact:** `DeprecationWarning` hoje, quebra em atualização futura; `utcnow()` devolve datetime *naive*, o que já gera comparações ambíguas de fuso na regra de "overdue".
- **Recommendation:** Substituir por `db.session.get(...)` e por um helper `utcnow()` central baseado em `datetime.now(timezone.utc)`. Ver catálogo — *Detecção de APIs deprecated*.

### [MEDIUM] Coleções sem paginação e CORS irrestrito
- **File:** `routes/task_routes.py:14`, `routes/task_routes.py:266`, `routes/user_routes.py:12`, `routes/report_routes.py:30`, `app.py:15`
- **Description:** `GET /tasks`, `GET /tasks/search`, `GET /users` e `/reports/summary` fazem `.all()` sem `limit`/`offset` e serializam a tabela inteira. `CORS(app)` (`app.py:15`) libera qualquer origem para todos os endpoints — incluindo `POST /login` e `DELETE /users/<id>`, que não têm auth. Ainda em `search_tasks:252`, o termo do usuário entra no `LIKE` sem escapar `%`/`_` (não é SQL injection, pois o SQLAlchemy parametriza, mas os wildcards do usuário são interpretados).
- **Impact:** Um crescimento de dados degrada a API e a memória do processo; CORS aberto permite que qualquer site execute as ações destrutivas no navegador da vítima.
- **Recommendation:** Paginação com `page`/`per_page` e envelope de metadados; `CORS(app, origins=os.getenv('CORS_ORIGINS'))`; escapar wildcards no termo de busca. Ver playbook padrões 6 e 7.

### [LOW] L1 — Nomenclatura de uma letra
- **File:** `routes/task_routes.py:16`, `routes/task_routes.py:268`, `routes/user_routes.py:14`, `routes/user_routes.py:161`, `routes/report_routes.py:33`, `routes/report_routes.py:55`, `routes/report_routes.py:161`, `routes/report_routes.py:24-28`, `models/category.py:14`, `seed.py:79`
- **Description:** Laços e variáveis usam `t`, `u`, `c`, `n`, `d`, `td`, `cat`, `s`, `p`, `pwd`, e as contagens por prioridade são `p1` a `p5` (`report_routes.py:24-28`) — sem qualquer indicação de que 1 é "critical" e 5 é "minimal" (mapeamento que só aparece 60 linhas abaixo, em 83-89).
- **Impact:** Leitura mais lenta e maior chance de erro ao editar laços aninhados.
- **Recommendation:** Renomear para `task`, `user`, `category`, `notification`, `task_data`, `password`, e trocar `p1..p5` por um dicionário de contagem por prioridade nomeada.

### [LOW] `if/else` verboso apenas para retornar booleano
- **File:** `models/user.py:34-38`, `models/task.py:38-48`, `models/task.py:50-60`, `utils/helpers.py:19-23`, `utils/helpers.py:52-55`
- **Description:** `User.is_admin` faz `if self.role == 'admin': return True else: return False`; `Task.validate_status` e `validate_priority` seguem o mesmo padrão; `Task.is_overdue` (50-60) aninha três `if/else` com quatro `return False` redundantes para expressar uma única condição booleana.
- **Impact:** Verbosidade que esconde a regra; `is_overdue` em particular fica difícil de conferir visualmente.
- **Recommendation:** Retornar a expressão diretamente (`return self.role == 'admin'`; `return bool(self.due_date) and self.due_date < utcnow() and self.status not in TERMINAL_STATUSES`).

### [LOW] Imports não utilizados
- **File:** `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `utils/helpers.py:3-7`, `models/task.py:3`
- **Description:** `app.py:7` importa `os, sys, json` e usa apenas `datetime`; `task_routes.py:7` importa `json, os, sys, time` — nenhum usado; `user_routes.py:6` importa `hashlib, json` sem uso (o hash está no model); `report_routes.py:7` importa `format_date` e `calculate_percentage` que não são chamados, e `json` na linha 8; `helpers.py:3-7` importa `os, json, sys, math, hashlib` sem uso; `models/task.py:3` importa `json` sem uso. Ainda em `helpers.py:31-34`, `generate_id()` faz `import uuid` dentro do corpo da função — e a função nunca é chamada.
- **Impact:** Ruído; falso sinal sobre as dependências reais de cada módulo.
- **Recommendation:** Remover todos os imports não usados e o código morto (`generate_id`, `sanitize_string`, `format_date`); mover imports para o topo.

### [LOW] L2 — Mensagens e artefatos enganosos
- **File:** `routes/user_routes.py:207-211`, `services/notification_service.py:1-48`, `README.md:3`
- **Description:** `POST /login` responde `'message': 'Login realizado com sucesso'` acompanhado de `'token': 'fake-jwt-token-<id>'` — o nome admite que o token é falso, mas a resposta se apresenta como autenticação bem-sucedida ao cliente. O `NotificationService` inteiro sugere que a aplicação envia e-mails de atribuição e de atraso, mas não é instanciado em nenhum ponto: nenhuma notificação é enviada. O `README.md:3` descreve o projeto como tendo "alguma separação de camadas", o que superestima pastas que não separam responsabilidades de fato.
- **Impact:** Consumidor da API acredita ter um token válido; leitor do código acredita que notificações funcionam; o diagnóstico real da arquitetura fica mascarado.
- **Recommendation:** Emitir JWT real (ver finding CRITICAL de autenticação) ou retornar 501 explícito; ligar o `NotificationService` a um evento real de atribuição/atraso ou removê-lo; ajustar o README após a refatoração.

## Rodapé
- **Total de findings:** 19
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
