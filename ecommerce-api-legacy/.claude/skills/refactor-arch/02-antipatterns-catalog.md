# 02 — Catálogo de Anti-Patterns

Catálogo de referência usado na **Fase 2 (Auditoria)**. Cada anti-pattern traz: **nome**,
**severidade**, **descrição**, **sinais de detecção** (com exemplos de código), **impacto** e
**recomendação de correção**.

Severidades:
- **CRITICAL** — risco de segurança grave ou falha estrutural que compromete o sistema.
- **HIGH** — viola fortemente a arquitetura; alto custo de manutenção ou bug provável.
- **MEDIUM** — problema real de qualidade que degrada manutenibilidade/consistência.
- **LOW** — melhoria de legibilidade/estilo; baixo risco imediato.

---

## CRITICAL

### C1. God Class / God Method
**Severidade:** CRITICAL
**Descrição:** Uma única classe ou função concentra responsabilidades demais — roteamento, acesso a
dados, regras de negócio, integrações e serialização. Vira o "centro de tudo".

**Sinais de detecção:**
- Classe/arquivo com centenas de linhas e dezenas de métodos.
- Um "Manager"/"Service" que registra rotas **e** executa SQL **e** processa pagamento.
```js
class AppManager {
  initDb() { /* cria tabelas */ }
  setupRoutes(app) {
    app.post('/api/checkout', (req,res) => { /* validação + SQL + pagamento + auditoria */ });
    app.get('/api/admin/financial-report', ...);
    app.delete('/api/users/:id', ...);
  }
}
```
```python
def criar_pedido(usuario_id, itens):
    # valida estoque, calcula total, insere pedido, insere itens, atualiza estoque... tudo aqui
```
**Impacto:** impossível testar em isolamento; qualquer mudança tem efeito colateral; alto acoplamento.
**Recomendação:** quebrar em camadas — Controller (fluxo), Service (regra de negócio), Model/Repository (dados). Ver playbook padrões 1 e 2.

### C2. Hardcoded Credentials / Secrets
**Severidade:** CRITICAL
**Descrição:** Senhas, chaves de API, secret keys e credenciais de banco escritas diretamente no código-fonte.

**Sinais de detecção:**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```
```js
const config = {
  dbPass: "senha_super_secreta_prod_123",
  paymentGatewayKey: "pk_live_1234567890abcdef"
};
```
```python
self.email_password = 'senha123'
```
**Impacto:** vazamento de credenciais ao versionar; comprometimento total do ambiente de produção;
impossível rotacionar segredos sem alterar código.
**Recomendação:** mover para variáveis de ambiente (`.env` + `os.getenv`/`process.env`), nunca versionar
o `.env`, adicionar `.env.example`. Ver playbook padrão 3.

---

## HIGH

### H1. Lógica de negócio no Controller / na Rota
**Severidade:** HIGH
**Descrição:** Regras de negócio (cálculo de totais, descontos, decisão de pagamento, notificações)
implementadas dentro do handler HTTP, em vez de uma camada de Service/Model.

**Sinais de detecção:**
```python
# dentro do controller de pedido
print("ENVIANDO EMAIL: Pedido criado...")
print("ENVIANDO SMS: Seu pedido foi recebido!")
```
```js
let status = cc.startsWith("4") ? "PAID" : "DENIED"; // regra de pagamento na rota
```
**Impacto:** regra não reutilizável, não testável fora do HTTP; duplicação entre endpoints.
**Recomendação:** extrair a regra para Service/Model; o controller apenas orquestra request → service → response. Ver playbook padrão 2.

### H2. Acoplamento forte sem Injeção de Dependência
**Severidade:** HIGH
**Descrição:** Componentes instanciam suas dependências diretamente (conexão de banco global, `new X()`
dentro da classe), impossibilitando substituição/mocks.

**Sinais de detecção:**
```python
db_connection = None            # conexão global no módulo
def get_db(): global db_connection; ...
```
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); } // dependência fixa
}
```
**Impacto:** testes impossíveis sem banco real; troca de implementação exige reescrever a classe.
**Recomendação:** injetar dependências via construtor/parâmetro; depender de abstrações. Ver playbook padrão 9.

### H3. SQL dentro de loop (N+1 queries)
**Severidade:** HIGH
**Descrição:** Consultas executadas dentro de um laço, gerando uma query por item — o clássico N+1.

**Sinais de detecção:**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
```js
courses.forEach(c => {
  this.db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], ... )
});
```
**Impacto:** performance degrada linearmente com o volume; centenas de round-trips ao banco.
**Recomendação:** usar JOIN, `IN (...)`, ou eager loading do ORM para buscar em lote. Ver playbook padrão 6.

---

## MEDIUM

### M1. Validação ausente ou inconsistente nas rotas
**Severidade:** MEDIUM
**Descrição:** Endpoints que aceitam entrada sem validar tipo, formato ou obrigatoriedade — ou que
validam de forma ad-hoc e repetida em cada handler.

**Sinais de detecção:**
```js
app.delete('/api/users/:id', (req,res) => {
  let id = req.params.id;                 // sem validar se é número / se existe
  this.db.run("DELETE FROM users WHERE id = ?", [id], ...);
});
```
```python
dados = request.get_json()
usuario_id = dados.get("usuario_id")      # aceita qualquer coisa
```
**Impacto:** dados corrompidos, erros 500 evitáveis, comportamento imprevisível.
**Recomendação:** camada de validação (schema/middleware) reutilizável antes do controller. Ver playbook padrão 7.

### M2. Magic Numbers / Magic Strings
**Severidade:** MEDIUM
**Descrição:** Números e strings literais com significado de negócio espalhados pelo código, sem nome.

**Sinais de detecção:**
```python
if faturamento > 10000: desconto = faturamento * 0.1
elif faturamento > 5000: desconto = faturamento * 0.05
```
```js
for(let i = 0; i < 10000; i++) { ... }   // 10000 sem explicação
```
**Impacto:** difícil entender a regra; mudança exige caça a literais duplicados.
**Recomendação:** extrair para constantes nomeadas / configuração. Ver playbook padrão 8.

### M3. Duplicação de código
**Severidade:** MEDIUM
**Descrição:** Blocos praticamente idênticos repetidos em vários pontos (serialização, cálculo de
"overdue", montagem de resposta).

**Sinais de detecção:**
```python
# bloco repetido em get_tasks, get_task, get_user_tasks:
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            task_data['overdue'] = True
```
```python
# get_todos_pedidos e get_pedidos_usuario têm o mesmo corpo de montagem
```
**Impacto:** correção precisa ser feita em N lugares; risco de divergência.
**Recomendação:** extrair função/método único (DRY); centralizar serialização em to_dict/serializer. Ver playbook padrões 1 e 5.

---

## LOW

### L1. Nomenclatura ruim de variáveis
**Severidade:** LOW
**Descrição:** Nomes de uma letra ou abreviações crípticas que não revelam intenção.

**Sinais de detecção:**
```js
let u = req.body.usr;
let e = req.body.eml;
let p = req.body.pwd;
let cc = req.body.card;
```
```python
def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    q = ...  # 'q', 'd', 'x'
```
**Impacto:** leitura e manutenção mais lentas; maior chance de erro.
**Recomendação:** renomear para nomes descritivos (`user`, `email`, `password`, `card`).

### L2. Comentários desatualizados / enganosos
**Severidade:** LOW
**Descrição:** Comentários (ou mensagens/prints) que não refletem o que o código faz — ou que
"documentam" um comportamento errado como se fosse normal.

**Sinais de detecção:**
```js
res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
```
```python
"ambiente": "producao",   # em código com DEBUG=True e SQLite local
```
**Impacto:** engana quem lê; mascara bugs e dívidas técnicas.
**Recomendação:** remover/atualizar comentários e mensagens; que o código e as mensagens digam a verdade.

---

## Detecção de APIs deprecated

Além dos anti-patterns acima, sinalizar uso de APIs obsoletas:

- **Express `bodyParser`**: uso de `app.use(bodyParser.json())` / `require('body-parser')` quando o
  Express **4.16+** já traz `express.json()` e `express.urlencoded()` embutidos. Deprecado — deve usar
  `app.use(express.json())`. Ver playbook padrão 10.
- **Flask `@app.before_first_request`**: removido no Flask 2.3+.
- **Node `crypto` caseiro / `new Buffer()`**: `new Buffer()` está deprecado (usar `Buffer.from()`), e
  hashing caseiro (loops de base64) nunca deve substituir `bcrypt`/`crypto.scrypt`.
- **`datetime.utcnow()`** (Python 3.12+): marcado como deprecado em favor de `datetime.now(timezone.utc)`.
- **SQLAlchemy `Query.get()`**: `Model.query.get(id)` está deprecado no SQLAlchemy 2.x em favor de `db.session.get(Model, id)`.

Para cada API deprecated encontrada, registrar como finding (geralmente MEDIUM) com arquivo:linha e a
substituição recomendada.
