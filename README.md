# Skill de Auditoria e Refatoração Arquitetural (`/refactor-arch`)

Este repositório entrega uma **Skill para Claude Code** que audita e refatora projetos backend
legados, migrando-os para o padrão **MVC** de forma **agnóstica de tecnologia** (Python/Flask e
Node.js/Express). A skill executa em 3 fases — **Análise → Auditoria → Refatoração** — com um ponto
de pausa obrigatório para confirmação humana antes de modificar qualquer arquivo.

- **Skill:** `.claude/skills/refactor-arch/` (presente nos 3 projetos, cópia idêntica)
- **Comando:** `/refactor-arch`
- **Arquivos de referência:** `SKILL.md` + `01-project-analysis.md`, `02-antipatterns-catalog.md`, `03-audit-report-template.md`, `04-mvc-guidelines.md`, `05-refactoring-playbook.md`
- **Relatórios de auditoria:** `reports/audit-project-1.md`, `reports/audit-project-2.md`, `reports/audit-project-3.md`

---

## A) Análise Manual

Análise manual do código dos 3 projetos. Para cada problema: severidade, `arquivo:linha` e
justificativa de impacto. (Os relatórios completos, gerados no formato do template da skill, estão em `reports/`.)

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)

| Severidade | Problema | Arquivo:linha | Justificativa de impacto |
|-----------|----------|---------------|--------------------------|
| CRITICAL | SQL Injection por concatenação de strings | `models.py:28,47-50,110,289-297` | Todas as queries concatenam entrada do usuário; permite bypass de login e manipulação total do banco. |
| CRITICAL | SECRET_KEY hardcoded e exposta no `/health` | `app.py:7`, `controllers.py:289` | Segredo versionado **e** devolvido no JSON do health check — compromete sessões/assinaturas. |
| CRITICAL | Endpoints `/admin/query` e `/admin/reset-db` sem auth | `app.py:47-78` | Executam SQL arbitrário e apagam o banco sem autenticação — destruição/roubo total de dados. |
| HIGH | Lógica de negócio/notificação no controller | `controllers.py:208-210,247-250` | E-mail/SMS/push simulados via `print` dentro do handler; regra não testável nem reutilizável. |
| HIGH | SQL dentro de loop (N+1) | `models.py:187-199,219-231` | Query de itens e de produto por iteração; performance degrada com o volume. |
| MEDIUM | Senhas em texto puro (armazenadas e retornadas) | `models.py:122-131,80-86`, `database.py:76-78` | Credenciais vazam no banco e nas respostas de listagem de usuários. |
| MEDIUM | Magic numbers nas faixas de desconto | `models.py:256-262` | Regra de negócio obscura (`10000/0.1`...) difícil de manter. |
| MEDIUM | Validação duplicada nos controllers | `controllers.py:28-54,72-90` | Blocos repetidos entre criar/atualizar produto; risco de divergência. |
| LOW | `DEBUG=True` e `host=0.0.0.0` no código | `app.py:8,88` | Debugger e stack traces expostos em produção. |
| LOW | Prints como log / mensagens enganosas | `controllers.py:8,179`, `app.py:56` | Vaza e-mail de login em log e informa `"ambiente":"producao"` falso. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS)

| Severidade | Problema | Arquivo:linha | Justificativa de impacto |
|-----------|----------|---------------|--------------------------|
| CRITICAL | Credenciais/secrets hardcoded (incl. `pk_live`) | `src/utils.js:1-7` (+ log em `AppManager.js:45`) | Chave **live** de pagamento e senha de banco versionadas e logadas — risco financeiro direto. |
| CRITICAL | God Class `AppManager` (rotas+dados+negócio+auditoria) | `src/AppManager.js:4-139` | 141 linhas concentrando tudo, com callbacks aninhados em 5 níveis; intestável. |
| HIGH | Regra de pagamento embutida na rota | `src/AppManager.js:43-64` | `cc.startsWith("4") ? "PAID" : "DENIED"` inline; regra acoplada ao HTTP. |
| HIGH | N+1 no relatório financeiro | `src/AppManager.js:83-128` | Queries aninhadas por curso/matrícula com contadores manuais; explosão de queries. |
| HIGH | Acoplamento sem DI (banco fixo em memória) | `src/AppManager.js:5-8` | `new sqlite3.Database(':memory:')` no construtor; sem mock, dados voláteis. |
| MEDIUM | Validação ausente e integridade quebrada no delete | `src/AppManager.js:131-137` | Remove usuário deixando enrollments/payments órfãos (a resposta admite isso). |
| MEDIUM | Criptografia caseira de senha | `src/utils.js:17-23` (uso em `AppManager.js:68`) | `badCrypto` (loop base64, 10 chars) não é hash seguro. |
| LOW | Nomenclatura críptica (`u`,`e`,`p`,`cc`) | `src/AppManager.js:29-33` | Leitura difícil e propensa a erro. |
| LOW | Estado global mutável / dead code | `src/utils.js:9-10,25` | `globalCache`/`totalRevenue` globais; `totalRevenue` nunca atualizado. |

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager — MVC parcial)

| Severidade | Problema | Arquivo:linha | Justificativa de impacto |
|-----------|----------|---------------|--------------------------|
| HIGH | Hash MD5 + secret key/senha de e-mail hardcoded | `models/user.py:29,32`, `app.py:13`, `services/notification_service.py:10` | MD5 sem salt é quebrável; secrets versionados. |
| HIGH | Serialização/regra duplicada + N+1 | `routes/task_routes.py:16-59,42,51`, `routes/report_routes.py:53-68`, `routes/user_routes.py:159-181` | Cálculo de "overdue" repetido e queries por item; DRY e performance. |
| MEDIUM | `to_dict` do usuário expõe senha | `models/user.py:16-25` (uso em `user_routes.py:33,85,209`) | Hash de senha vaza nas respostas. |
| MEDIUM | Validação dispersa e helper não usado | `routes/*`, `utils/helpers.py:57-108` | `process_task_data` existe mas não é usado; validações inline duplicadas. |
| MEDIUM | `except:` nu silenciando erros | `task_routes.py:62-63`, `user_routes.py:130-132`, `report_routes.py:186-188` | Erros reais ficam invisíveis; difícil diagnosticar. |
| LOW | `if/else` verboso retornando booleano | `models/user.py:34-38`, `models/task.py:38-60` | Verbosidade desnecessária. |
| LOW | Imports não usados + `datetime.utcnow()` deprecado | `task_routes.py:7`, `app.py:7`, `utils/helpers.py:1-7` | Ruído e deprecation warnings (Python 3.12+). |

---

## B) Construção da Skill

### Decisões de design

- **SKILL.md como orquestrador de 3 fases.** O `SKILL.md` descreve *o que* fazer em cada fase e
  *quando* ler cada arquivo de referência — evitando sobrecarregar o contexto do agente lendo tudo de
  uma vez. Cada fase carrega apenas os arquivos que precisa (Fase 1 → `01`; Fase 2 → `01/02/03`;
  Fase 3 → `04/05`).
- **5 arquivos de referência, um por área de conhecimento** exigida pelo enunciado:
  `01-project-analysis` (heurísticas de detecção), `02-antipatterns-catalog` (catálogo),
  `03-audit-report-template` (template do relatório), `04-mvc-guidelines` (arquitetura alvo) e
  `05-refactoring-playbook` (transformações). Isso mantém cada arquivo coeso e fácil de evoluir.
- **Pausa obrigatória entre Auditoria e Refatoração.** A Fase 2 termina com
  `Prosseguir com a refatoração? [s/n]` e a regra explícita de que **nenhum arquivo é modificado**
  sem `s`. Segurança e controle humano no loop.

### Anti-patterns incluídos e por quê

O catálogo tem **10 anti-patterns** (acima do mínimo de 8), distribuídos por severidade e escolhidos
por serem exatamente os que aparecem nos 3 projetos-alvo:

- **CRITICAL:** God Class/Method e Hardcoded Secrets — os problemas de maior risco (segurança/estrutura), presentes em `AppManager.js` e nas secrets de todos os projetos.
- **HIGH:** Lógica no controller, Acoplamento sem DI e N+1 — violações fortes de MVC/SOLID e o gargalo de performance mais comum.
- **MEDIUM:** Validação ausente, Magic Numbers e Duplicação — problemas de padronização/manutenção recorrentes.
- **LOW:** Nomenclatura ruim e Comentários/mensagens enganosos — legibilidade.
- **APIs deprecated:** seção dedicada (Express `bodyParser`, `new Buffer()`, `datetime.utcnow()`, `Query.get()` do SQLAlchemy 2.x) com o equivalente moderno — atendendo ao requisito de detecção de APIs obsoletas.

### Como a skill é agnóstica de tecnologia

- Toda detecção é feita **pelo conteúdo** dos arquivos (sinais de linguagem/framework/banco), não pela
  extensão — ver `01-project-analysis.md`.
- Catálogo, guidelines e playbook trazem exemplos **lado a lado** para Python/Flask e Node.js/Express.
- A estrutura MVC alvo (`config/models/views/controllers/middlewares`) é descrita para as duas stacks.
- Validada nos 3 projetos: dois Python/Flask (um monolítico, um MVC parcial) e um Node.js/Express.

### Desafios encontrados

- **Onde mora a "View" numa API REST:** não há template HTML. Resolvido definindo a camada View como
  **rotas + serialização** da resposta JSON.
- **Projeto já parcialmente organizado (Projeto 3):** a skill precisa achar problemas mesmo com
  `models/routes/services`. Resolvido com heurísticas que detectam MVC *parcial* e miram refinamentos
  (duplicação, N+1, exposição de senha, `except` nu) e não só desestruturação total.
- **Ruído de arquivos gerados:** apenas os `.md` fazem parte do entregável em `reports/` (PDF/DOCX
  auto-gerados foram descartados para manter o repositório limpo).

---

## C) Resultados

### Resumo dos relatórios de auditoria (findings por severidade)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---------|:--------:|:----:|:------:|:---:|:-----:|
| 1 — code-smells-project | 3 | 2 | 3 | 2 | **10** |
| 2 — ecommerce-api-legacy | 2 | 3 | 2 | 2 | **9** |
| 3 — task-manager-api | 0 | 2 | 3 | 2 | **7** |

Todos atendem ao mínimo exigido (Projetos 1 e 2 ≥ 8 findings; Projeto 3 ≥ 5, mais organizado).

### Comparação antes/depois da estrutura de diretórios (alvo proposto pela skill)

**Projeto 1 — code-smells-project**
```
ANTES                          DEPOIS (alvo MVC)
app.py                         src/config/config.py        (secrets em .env)
controllers.py                 src/models/{product,user,order}.py
models.py (DAO+SQL)            src/views/{product,user,order}_routes.py
database.py (conexão global)  src/controllers/{...}_controller.py
                               src/middlewares/error_handler.py
                               app.py (create_app / composition root)
```

**Projeto 2 — ecommerce-api-legacy**
```
ANTES                          DEPOIS (alvo MVC)
src/app.js                     src/config/index.js         (.env)
src/AppManager.js (God Class)  src/models/{user,course,payment}Model.js
src/utils.js (secrets/cache)   src/views/{checkout,report,user}Routes.js
                               src/controllers/{...}Controller.js
                               src/services/paymentService.js
                               src/middlewares/{errorHandler,validate}.js
                               app.js (monta routers + middlewares)
```

**Projeto 3 — task-manager-api**
```
ANTES                          DEPOIS (alvo MVC refinado)
models/ routes/ services/      src/config/  (secrets em .env, sem MD5)
utils/  app.py                 src/models/  (to_dict sem senha)
                               src/views/   (routes finas)
                               src/controllers/ (fluxo)
                               src/services/    (regra + N+1 resolvido)
                               src/middlewares/error_handler.py (sem except nu)
```

### Checklist de validação (por item do enunciado)

**Entregáveis / requisitos da skill:**
- [✓] Skill em `.claude/skills/refactor-arch/` presente nos 3 projetos (cópia idêntica — md5 conferido)
- [✓] `SKILL.md` com 3 fases sequenciais (Análise → Auditoria → Refatoração)
- [✓] 5 áreas de conhecimento cobertas nos arquivos de referência (01 a 05)
- [✓] Catálogo com ≥ 8 anti-patterns e severidade distribuída (10 no total)
- [✓] Detecção de APIs deprecated incluída (seção dedicada)
- [✓] Playbook com ≥ 8 padrões de transformação antes/depois (10 no total)
- [✓] Fase 2 pausa e pede confirmação `[s/n]` antes de modificar arquivos
- [✓] Fase 3 especifica validação (boot da aplicação + endpoints respondendo)
- [✓] Relatórios em `reports/audit-project-{1,2,3}.md` seguindo o template
- [✓] Cada finding com `arquivo:linha` exatos e ordenado por severidade
- [✓] `README.md` com as 4 seções (A, B, C, D)

**Execução da refatoração (Fase 3) nos projetos:**
- [✗] Código-fonte dos 3 projetos efetivamente reestruturado para `src/` — **requer execução manual da skill** (ver seção D)
- [✗] Aplicações reiniciadas e endpoints revalidados após refatoração automática — **requer execução manual**

> **Nota sobre execução manual.** Este repositório entrega a **skill completa, os relatórios de
> auditoria (Fase 2) e a documentação**. A **Fase 3 (refatoração automática do código-fonte)** é um
> passo interativo do Claude Code que roda no ambiente do usuário (o comando `/refactor-arch` requer o
> Claude Code instalado e autenticado, e a confirmação humana `[s/n]`). Por isso, a reestruturação
> física dos arquivos de cada projeto para `src/` deve ser disparada localmente conforme o passo a
> passo da seção **D)**. Os relatórios e a estrutura-alvo documentada permitem reproduzir a Fase 3 de
> forma determinística.

### Observações sobre o comportamento em stacks diferentes

- **Python monolítico (Projeto 1):** a skill mira primeiro segurança (SQL injection, secrets) e a
  ausência total de camadas.
- **Node.js God Class (Projeto 2):** foco em quebrar a `AppManager`, resolver callback hell e o N+1 do
  relatório.
- **Python MVC parcial (Projeto 3):** foco em refinamento (duplicação, exposição de senha, `except`
  nu, deprecations), provando que a skill se adapta ao nível de organização existente.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado ([docs oficiais](https://docs.anthropic.com/en/docs/claude-code)).
- **Python 3.10+** (Projetos 1 e 3) e **Node.js 18+** (Projeto 2).
- Dependências dos projetos:
  - Projeto 1: `pip install -r code-smells-project/requirements.txt`
  - Projeto 2: `cd ecommerce-api-legacy && npm install`
  - Projeto 3: `pip install -r task-manager-api/requirements.txt`
- **Variáveis de ambiente:** após a refatoração, cada projeto usa um `.env` (não versionado). Crie a
  partir do `.env.example` que a Fase 3 gera, definindo `SECRET_KEY`, credenciais de banco/gateway e
  `DEBUG=false`.

### Comandos para executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask (E-commerce)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (LMS)   (a skill já está copiada em .claude/skills/)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask (Task Manager)
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução: a **Fase 1** imprime o resumo em caixa ASCII; a **Fase 2** gera o relatório e
pergunta `Prosseguir com a refatoração? [s/n]`; responda **`s`** para a **Fase 3** reestruturar o
projeto para `src/` (MVC) e validar.

### Como validar que a refatoração funcionou

1. **A aplicação inicia sem erros:**
   - Projeto 1/3: `python app.py` → deve subir em `http://localhost:5000`.
   - Projeto 2: `npm start` → deve subir em `http://localhost:3000`.
2. **Os endpoints originais respondem:**
   - Projeto 1: `curl http://localhost:5000/produtos` e `GET /health`.
   - Projeto 2: use o `ecommerce-api-legacy/api.http` (checkout, financial-report, delete user).
   - Projeto 3: `curl http://localhost:5000/tasks`, `/users`, `/reports/summary`.
3. **Confira o checklist da Fase 3** impresso no resumo final (config sem hardcoded, models criados,
   rotas separadas, error handling centralizado, endpoints ok).

### Passo a passo do que fazer manualmente após executar a skill

1. Rode `/refactor-arch` no projeto e revise o relatório da **Fase 2** (compare com `reports/`).
2. Responda **`s`** para autorizar a **Fase 3**.
3. Após a refatoração: crie o `.env` a partir do `.env.example` gerado e preencha os segredos reais.
4. Instale dependências novas se a skill adicionou (ex.: `python-dotenv`, remoção de `body-parser`).
5. Suba a aplicação e execute a bateria de validação acima (boot + endpoints).
6. Rode os testes/`api.http`; se algum endpoint divergir, ajuste e reexecute (2–4 iterações são normais).
7. Faça commit do código refatorado de cada projeto.

---

## Estrutura do repositório

```
mba-ia-refactor-projects-skill/
├── README.md
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
├── code-smells-project/
│   └── .claude/skills/refactor-arch/{SKILL.md,01..05.md}
├── ecommerce-api-legacy/
│   └── .claude/skills/refactor-arch/{SKILL.md,01..05.md}
└── task-manager-api/
    └── .claude/skills/refactor-arch/{SKILL.md,01..05.md}
```
