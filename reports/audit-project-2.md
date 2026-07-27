# Relatório de Auditoria — ecommerce-api-legacy

## Cabeçalho
- **Projeto:** `ecommerce-api-legacy` ("Frankenstein LMS")
- **Stack:** Node.js / Express 4.18.2 / SQLite (`sqlite3` 5.1.6, banco `:memory:`, SQL manual em callbacks)
- **Arquivos analisados:** `src/app.js`, `src/AppManager.js`, `src/utils.js`, `package.json`, `api.http`
- **Linhas de código:** ~180 (app.js 14, AppManager.js 141, utils.js 25)
- **Domínio:** Plataforma de cursos/LMS — usuários, cursos, matrículas (enrollments), pagamentos e logs de auditoria
- **Data da auditoria:** 2026-07-27

## Summary (contagem por severidade)
| Severidade | Quantidade |
|------------|------------|
| CRITICAL   | 2          |
| HIGH       | 3          |
| MEDIUM     | 2          |
| LOW        | 2          |
| **TOTAL**  | **9**      |

## Findings
> Ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW).

### [CRITICAL] Hardcoded Credentials / Secrets
- **File:** `src/utils.js:1-7`
- **Description:** Objeto `config` com credenciais de produção em texto puro: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser`. Ainda são logadas em runtime (`AppManager.js:45` imprime a chave do gateway no console).
- **Impact:** Vazamento de credenciais e da chave **live** do gateway de pagamento ao versionar/loggar — fraude financeira direta.
- **Recommendation:** Mover tudo para `.env` (`process.env`), remover o `console.log` da chave e adicionar `.env` ao `.gitignore`. Ver playbook padrão 3.

### [CRITICAL] God Class concentrando rotas, dados, negócio e integrações
- **File:** `src/AppManager.js:4-139`
- **Description:** A classe `AppManager` cria o banco (`initDb`), registra **todas** as rotas (`setupRoutes`), executa SQL, decide o pagamento e grava auditoria — tudo em uma classe única de 141 linhas com callbacks aninhados em até 5 níveis (checkout, linhas 28-78).
- **Impact:** Impossível testar/isolar; qualquer mudança tem efeito colateral; "callback hell" ilegível.
- **Recommendation:** Quebrar em Models (user/course/payment), Controllers, Routers e Services; usar async/await. Ver playbook padrões 1, 2 e 4.

### [HIGH] Lógica de negócio de pagamento embutida na rota
- **File:** `src/AppManager.js:43-64`
- **Description:** A decisão de pagamento é feita inline dentro do handler de checkout: `let status = cc.startsWith("4") ? "PAID" : "DENIED";` (linha 46), seguida de inserções encadeadas de enrollment/payment/audit.
- **Impact:** Regra de pagamento não reutilizável nem testável; validação de cartão fictícia e acoplada ao HTTP.
- **Recommendation:** Extrair um `PaymentService`/`CheckoutService`; o controller apenas orquestra. Ver playbook padrão 2.

### [HIGH] SQL dentro de loop (N+1 queries) no relatório financeiro
- **File:** `src/AppManager.js:83-128`
- **Description:** `/api/admin/financial-report` percorre `courses.forEach` e, para cada curso, consulta enrollments; para cada enrollment consulta usuário e pagamento (queries aninhadas nas linhas 92, 104, 106), com controle manual de contadores (`coursesPending`/`enrPending`).
- **Impact:** Explosão de queries (cursos×matrículas×2); performance péssima e código frágil de sincronização por contadores.
- **Recommendation:** Uma query com JOINs entre courses/enrollments/users/payments e agregação em memória. Ver playbook padrão 6.

### [HIGH] Acoplamento forte sem Injeção de Dependência
- **File:** `src/AppManager.js:5-8`
- **Description:** O construtor instancia diretamente o banco (`this.db = new sqlite3.Database(':memory:')`), fixando a implementação e usando banco em memória.
- **Impact:** Impossível injetar mock/banco alternativo; dados perdidos a cada restart; testes dependem de estado real.
- **Recommendation:** Injetar a conexão/repos via construtor a partir de uma composition root. Ver playbook padrão 9.

### [MEDIUM] Validação ausente / integridade referencial quebrada
- **File:** `src/AppManager.js:131-137`
- **Description:** `DELETE /api/users/:id` remove o usuário sem validar o `id` e sem tratar enrollments/payments associados — a própria resposta admite: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` (linha 135).
- **Impact:** Registros órfãos, inconsistência de dados; entrada não validada.
- **Recommendation:** Validar o `id` (middleware) e tratar cascata/transação no Model. Ver playbook padrão 7.

### [MEDIUM] Criptografia de senha caseira e insegura
- **File:** `src/utils.js:17-23`, uso em `src/AppManager.js:68`
- **Description:** `badCrypto` faz um loop de 10.000 concatenações de base64 e retorna só 10 caracteres — não é hash criptográfico e há um magic number (`10000`) sem sentido.
- **Impact:** Senhas facilmente reversíveis/colidíveis; falsa sensação de segurança.
- **Recommendation:** Usar `bcrypt`/`crypto.scrypt` com salt; remover a função caseira. Ver anti-patterns C2/M2.

### [LOW] Nomenclatura críptica de variáveis
- **File:** `src/AppManager.js:29-33`
- **Description:** Variáveis de uma letra sem significado: `let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;`.
- **Impact:** Leitura difícil e propensa a erro.
- **Recommendation:** Renomear para `userName`, `email`, `password`, `courseId`, `card`. Ver anti-pattern L1.

### [LOW] Estado global mutável e variáveis mortas
- **File:** `src/utils.js:9-10`, `src/utils.js:25`
- **Description:** `globalCache = {}` e `totalRevenue = 0` como estado global compartilhado; `totalRevenue` é exportado mas nunca atualizado (dead code / cache global sem invalidação).
- **Impact:** Estado imprevisível entre requests, vazamento de memória e código enganoso.
- **Recommendation:** Remover estado global; usar cache dedicado com ciclo de vida ou camada de serviço. Ver anti-pattern L2.

## Rodapé
- **Total de findings:** 9
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
