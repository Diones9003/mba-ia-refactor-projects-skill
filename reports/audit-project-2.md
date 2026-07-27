# Relatório de Auditoria — ecommerce-api-legacy

## Cabeçalho
- **Projeto:** `ecommerce-api-legacy` ("Frankenstein LMS")
- **Stack:** Node.js / Express 4.18.2 / SQLite (`sqlite3` 5.1.6, banco `:memory:`, SQL manual em callbacks)
- **Arquivos analisados:** `src/app.js`, `src/AppManager.js`, `src/utils.js`, `package.json`, `api.http`
- **Linhas de código:** 180 (app.js 14, AppManager.js 141, utils.js 25)
- **Domínio:** Plataforma de cursos/LMS — usuários, cursos, matrículas (enrollments), pagamentos e logs de auditoria
- **Data da auditoria:** 2026-07-27

## Summary (contagem por severidade)
| Severidade | Quantidade |
|------------|------------|
| CRITICAL   | 2          |
| HIGH       | 3          |
| MEDIUM     | 4          |
| LOW        | 2          |
| **TOTAL**  | **11**     |

## Findings
> Ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW).

### [CRITICAL] Hardcoded Credentials / Secrets
- **File:** `src/utils.js:1-7`
- **Description:** Objeto `config` com credenciais de produção em texto puro: `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser`, `dbUser`. Pior: a chave **live** do gateway e o número do cartão são impressos no console em runtime (`src/AppManager.js:45`).
- **Impact:** Vazamento de credenciais ao versionar o repositório e nos logs de aplicação; comprometimento financeiro direto (chave `pk_live_`) e exposição de PCI (número de cartão em log). Impossível rotacionar segredos sem alterar código.
- **Recommendation:** Mover tudo para `.env` lido via `process.env`, criar `.env.example`, versionar `.gitignore` com `.env`, e remover o `console.log` que expõe cartão e chave. Ver playbook padrões 3 e 8.

### [CRITICAL] God Class concentrando rotas, dados, negócio e integrações
- **File:** `src/AppManager.js:4-141`
- **Description:** `AppManager` abre a conexão de banco no construtor (linha 7), cria schema e seeds (`initDb`, 10-23), registra **todas** as rotas (`setupRoutes`, 25-138), executa SQL cru, decide o resultado do pagamento e grava auditoria. O handler de checkout (28-78) chega a 5 níveis de callbacks aninhados e precisa do truque `const self = this` (linha 26) para escapar do rebind de `this` nos callbacks do sqlite3.
- **Impact:** Nenhuma parte é testável em isolamento; qualquer alteração tem efeito colateral em todo o arquivo; "callback hell" ilegível e propenso a erro de fluxo (ex.: resposta enviada duas vezes).
- **Recommendation:** Quebrar em Models (`user`, `course`, `enrollment`, `payment`, `audit_log`), Services (checkout/pagamento/relatório), Controllers e Routers; converter callbacks para `async/await` com um wrapper Promise sobre o driver. Ver playbook padrões 1, 2 e 4.

### [HIGH] Lógica de negócio de pagamento embutida na rota
- **File:** `src/AppManager.js:43-64`
- **Description:** A decisão de pagamento é feita inline no handler HTTP: `let status = cc.startsWith("4") ? "PAID" : "DENIED";` (linha 46), seguida das inserções encadeadas de enrollment → payment → audit_log e da chamada de cache (linha 59). Toda a regra de negócio do checkout vive dentro do callback da rota.
- **Impact:** Regra de pagamento não reutilizável nem testável fora do HTTP; a criação de matrícula, pagamento e auditoria não é transacional — uma falha no meio deixa dados parciais no banco.
- **Recommendation:** Extrair `PaymentGateway` (adapter) e `CheckoutService` (orquestração + transação); o controller apenas traduz request → service → response. Ver playbook padrão 2.

### [HIGH] SQL dentro de loop (N+1 queries) no relatório financeiro
- **File:** `src/AppManager.js:83-128`
- **Description:** `GET /api/admin/financial-report` faz `courses.forEach` e, para cada curso, consulta enrollments (linha 92); para cada enrollment consulta o usuário (linha 104) e o pagamento (linha 106). A sincronização é feita com contadores manuais (`coursesPending`, `enrPending`) e a ordem do array `report` depende de quem responde primeiro.
- **Impact:** Total de queries = 1 + N_cursos + 2×N_matrículas; degrada linearmente e estoura round-trips em volume real. O controle por contador é frágil: se `db.all` retornar erro, `enrollments` é `undefined` e a rota lança exceção não tratada (linha 93); a resposta também sai em ordem não determinística.
- **Recommendation:** Uma única query com `LEFT JOIN` entre courses/enrollments/users/payments e agregação em memória, preservando o mesmo formato de resposta. Ver playbook padrão 6.

### [HIGH] Acoplamento forte sem Injeção de Dependência
- **File:** `src/AppManager.js:1-8`
- **Description:** O construtor instancia diretamente a dependência concreta: `this.db = new sqlite3.Database(':memory:')`, com `require('sqlite3')` no topo do módulo. O `config` também é importado direto por `AppManager` e `app.js`, sem passagem por composition root.
- **Impact:** Impossível injetar mock, banco alternativo ou arquivo persistente; testes exigem o driver real; o caminho do banco fica fixo no código.
- **Recommendation:** Criar a conexão em uma camada de config/composition root (`src/app.js`) e injetar nos models via construtor; models e services dependem da abstração recebida. Ver playbook padrão 9 e guideline 4.

### [MEDIUM] Erros silenciados e ausência de error handling centralizado
- **File:** `src/AppManager.js:57`, `src/AppManager.js:92-106`, `src/AppManager.js:133`
- **Description:** Cada handler trata erro de forma ad-hoc com `res.status(500).send("Erro DB")`, e vários callbacks simplesmente **ignoram** o parâmetro `err`: a inserção do audit log (linha 57) responde sucesso mesmo se falhar, as queries de user/payment do relatório (104, 106) descartam o erro, e o `DELETE` (133) responde 200 independentemente do resultado. Não existe `try/catch`, nem middleware de erro, nem handler 404. Além disso, `if (err || !course)` (linha 38) mapeia erro de banco para **404**.
- **Impact:** Falhas reais são reportadas como sucesso ao cliente; diagnóstico impossível; status HTTP incorreto; mensagens de erro duplicadas e inconsistentes em cada rota.
- **Recommendation:** Middleware de erro central (`src/middlewares/error_handler.js`) + classe `AppError` com status, propagando erros via `next(err)`; distinguir erro de infraestrutura (500) de recurso não encontrado (404). Ver playbook padrão 5 e guideline 6.

### [MEDIUM] Validação ausente / integridade referencial quebrada
- **File:** `src/AppManager.js:35`, `src/AppManager.js:131-137`
- **Description:** A validação do checkout é um `if` inline que só checa presença (linha 35) — não valida formato de e-mail, tipo numérico de `c_id`, tamanho do cartão nem obrigatoriedade de `pwd`. Já `DELETE /api/users/:id` não valida se `id` é numérico nem se o usuário existe, e não trata os enrollments/payments associados — a própria resposta admite o problema (linha 135).
- **Impact:** Entradas inválidas chegam ao banco; registros órfãos em `enrollments`/`payments` corrompem o relatório financeiro; erros 500 evitáveis e respostas 200 para recursos inexistentes.
- **Recommendation:** Middleware de validação por schema reutilizável antes do controller; no model, tratar a remoção em cascata dentro de uma transação. Ver playbook padrão 7.

### [MEDIUM] Criptografia de senha caseira e insegura (+ magic number)
- **File:** `src/utils.js:17-23`, uso em `src/AppManager.js:68`
- **Description:** `badCrypto` concatena base64 do password 10.000 vezes e retorna apenas os 10 primeiros caracteres — não é hash criptográfico, não tem salt, é determinístico e o `10000` é um magic number sem propósito. O fallback `badCrypto(p || "123456")` (linha 68) atribui silenciosamente uma senha padrão quando `pwd` não é enviado.
- **Impact:** Senhas trivialmente reversíveis e altamente colidíveis (10 chars derivados de um alfabeto minúsculo); contas criadas com senha padrão conhecida; falsa sensação de segurança.
- **Recommendation:** Usar `crypto.scrypt`/`bcrypt` com salt por usuário, exigir `pwd` na validação de entrada e remover a função caseira. Ver anti-patterns C2/M2 e playbook padrão 7.

### [MEDIUM] Ausência de camada de View / respostas inconsistentes
- **File:** `src/AppManager.js:35-38`, `src/AppManager.js:48-60`, `src/AppManager.js:135`
- **Description:** Não existe camada de serialização: sucessos retornam JSON (`{ msg, enrollment_id }`), erros retornam **texto puro** (`"Bad Request"`, `"Curso não encontrado"`, `"Erro DB"`, `"Erro Matrícula"`), e o `DELETE` retorna uma frase em prosa. Cada handler monta a resposta à mão, inclusive a serialização do relatório (linhas 90, 112-115).
- **Impact:** Contrato de API imprevisível para o cliente (não dá para desserializar erros); duplicação da montagem de resposta em cada rota; mudança de formato exige caçar literais.
- **Recommendation:** Centralizar serialização em presenters/views e padronizar o envelope de erro no middleware, **preservando os payloads atuais** para não quebrar consumidores. Ver playbook padrões 4 e 5, e guideline 7.

### [LOW] Nomenclatura críptica de variáveis
- **File:** `src/AppManager.js:29-33`
- **Description:** Variáveis de uma/duas letras sem significado: `let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cid = req.body.c_id; let cc = req.body.card;`. O `e` é especialmente confuso por colidir com a convenção de "error". Uso de `let` onde nada é reatribuído.
- **Impact:** Leitura e manutenção mais lentas, maior chance de erro ao editar o bloco de callbacks aninhados.
- **Recommendation:** Renomear para `userName`, `email`, `password`, `courseId`, `card` e usar `const`. Nomes dos **campos do request body** (`usr`, `eml`, `pwd`, `c_id`, `card`) devem ser preservados por contrato. Ver anti-pattern L1.

### [LOW] Estado global mutável, dead code e mensagem enganosa
- **File:** `src/utils.js:9-10`, `src/utils.js:25`, `src/AppManager.js:135`
- **Description:** `globalCache = {}` é um cache global sem TTL nem invalidação, alimentado por `logAndCache` (12-15); `totalRevenue = 0` é exportado, importado em `AppManager.js:2` e **nunca usado nem atualizado** (dead code, e por ser primitivo a exportação nunca refletiria mudanças). A mensagem do `DELETE` documenta o bug como se fosse comportamento normal.
- **Impact:** Estado imprevisível entre requests e crescimento indefinido de memória; código enganoso para quem lê.
- **Recommendation:** Remover `totalRevenue`, encapsular o cache em um módulo com ciclo de vida próprio (ou eliminá-lo) e corrigir a mensagem junto com o comportamento. Ver anti-pattern L2.

## Rodapé
- **Total de findings:** 11
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
