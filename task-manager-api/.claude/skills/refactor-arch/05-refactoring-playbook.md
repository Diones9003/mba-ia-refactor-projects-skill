# 05 — Playbook de Refatoração

Padrões de transformação usados na **Fase 3**. Cada padrão traz: **anti-pattern alvo**, código
**ANTES** e **DEPOIS** e **passos de execução**. Os exemplos são realistas mas genéricos —
adapte à stack e ao domínio detectados.

---

## Padrão 1 — Extrair Model de God Class
**Anti-pattern alvo:** C1 (God Class), M3 (Duplicação)

**ANTES**
```js
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  setupRoutes(app) {
    app.post('/api/checkout', (req,res) => {
      this.db.run("INSERT INTO users (name,email,pass) VALUES (?,?,?)", [u,e,hash], ...);
      this.db.run("INSERT INTO enrollments (user_id,course_id) VALUES (?,?)", ...);
    });
  }
}
```

**DEPOIS**
```js
// src/models/userModel.js
class UserModel {
  constructor(db) { this.db = db; }
  create(name, email, passHash) {
    return new Promise((resolve, reject) =>
      this.db.run("INSERT INTO users (name,email,pass) VALUES (?,?,?)",
        [name, email, passHash], function (e) { e ? reject(e) : resolve(this.lastID); }));
  }
}
module.exports = UserModel;
```

**Passos de execução**
1. Identificar cada bloco de acesso a dados dentro da God Class.
2. Agrupar por entidade (users, courses, payments…).
3. Criar um model por entidade em `src/models/`, recebendo `db` injetado.
4. Substituir o SQL inline por chamadas ao model.

---

## Padrão 2 — Mover lógica de negócio do Controller para Service/Model
**Anti-pattern alvo:** H1 (Lógica no controller)

**ANTES**
```python
def criar_pedido():
    resultado = models.criar_pedido(usuario_id, itens)
    print("ENVIANDO EMAIL: Pedido criado...")
    print("ENVIANDO SMS: Seu pedido foi recebido!")
    return jsonify({"dados": resultado}), 201
```

**DEPOIS**
```python
# src/services/order_service.py
class OrderService:
    def __init__(self, order_model, notifier):
        self.order_model = order_model
        self.notifier = notifier
    def place_order(self, user_id, items):
        order = self.order_model.create(user_id, items)
        self.notifier.order_created(user_id, order)   # notificação isolada
        return order

# src/controllers/order_controller.py
def criar_pedido():
    data = request.get_json()
    order = order_service.place_order(data["usuario_id"], data["itens"])
    return jsonify({"dados": order, "sucesso": True}), 201
```

**Passos de execução**
1. Localizar regra de negócio (cálculos, decisões, side-effects) no handler.
2. Criar/estender um Service com a regra.
3. O controller passa a apenas extrair entrada, chamar o service e devolver a resposta.

---

## Padrão 3 — Remover credenciais hardcoded para .env
**Anti-pattern alvo:** C2 (Hardcoded secrets)

**ANTES**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
```

**DEPOIS**
```python
# .env  (não versionado)
SECRET_KEY=minha-chave-super-secreta-123

# src/config/config.py
import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")

# app.py
from src.config import config
app.config["SECRET_KEY"] = config.SECRET_KEY
```

**Passos de execução**
1. Grepar por segredos (`SECRET_KEY`, `password`, `pk_live`, `senha`).
2. Movê-los para `.env`; criar `.env.example` com as chaves vazias.
3. Ler via `os.getenv`/`process.env`; adicionar `.env` ao `.gitignore`.

---

## Padrão 4 — Criar Router separado para rotas
**Anti-pattern alvo:** C1 (God Class), organização de rotas

**ANTES**
```python
app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
app.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
# ...dezenas de add_url_rule no app.py
```

**DEPOIS**
```python
# src/views/product_routes.py
from flask import Blueprint
from src.controllers import product_controller
product_bp = Blueprint("products", __name__)
product_bp.add_url_rule("/produtos", "listar", product_controller.listar_produtos, methods=["GET"])
product_bp.add_url_rule("/produtos/<int:id>", "buscar", product_controller.buscar_produto, methods=["GET"])

# app.py
app.register_blueprint(product_bp)
```
```js
// src/views/checkoutRoutes.js
const router = require('express').Router();
router.post('/api/checkout', checkoutController.checkout);
module.exports = router;
// app.js: app.use(checkoutRoutes);
```

**Passos de execução**
1. Agrupar rotas por recurso.
2. Criar um Blueprint/Router por grupo em `src/views/`.
3. Registrar os routers no `app.py`/`app.js`.

---

## Padrão 5 — Centralizar error handling em middleware
**Anti-pattern alvo:** M3 (Duplicação), robustez

**ANTES**
```python
def listar_produtos():
    try:
        return jsonify({"dados": models.get_todos_produtos()}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500     # repetido em todo handler
```

**DEPOIS**
```python
# src/middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle(e):
        app.logger.exception(e)
        return {"erro": "Erro interno", "sucesso": False}, 500

# controller fica limpo:
def listar_produtos():
    return jsonify({"dados": product_model.find_all(), "sucesso": True}), 200
```

**Passos de execução**
1. Criar o handler central em `src/middlewares/`.
2. Registrá-lo na criação do app.
3. Remover os `try/except`/`try/catch` genéricos repetidos dos handlers.

---

## Padrão 6 — Eliminar query SQL dentro de loop (N+1)
**Anti-pattern alvo:** H3 (N+1 queries)

**ANTES**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**DEPOIS**
```python
# uma única query com JOIN
sql = """
  SELECT p.id AS pedido_id, ip.produto_id, pr.nome, ip.quantidade, ip.preco_unitario
  FROM pedidos p
  JOIN itens_pedido ip ON ip.pedido_id = p.id
  JOIN produtos pr    ON pr.id = ip.produto_id
"""
rows = cursor.execute(sql).fetchall()
# agrupar em memória por pedido_id
```

**Passos de execução**
1. Identificar loops que executam query por iteração.
2. Substituir por JOIN / `WHERE id IN (...)` / eager loading do ORM.
3. Agrupar/montar o resultado em memória.

---

## Padrão 7 — Adicionar validação de entrada nas rotas
**Anti-pattern alvo:** M1 (Validação ausente)

**ANTES**
```js
app.delete('/api/users/:id', (req,res) => {
  let id = req.params.id;                     // sem validar
  this.db.run("DELETE FROM users WHERE id = ?", [id], ...);
});
```

**DEPOIS**
```js
// src/middlewares/validate.js
const validateId = (req,res,next) => {
  const id = Number(req.params.id);
  if (!Number.isInteger(id) || id <= 0) return res.status(400).json({ error: "id inválido" });
  req.id = id; next();
};
// router: router.delete('/api/users/:id', validateId, userController.remove);
```
```python
# Python: schema Marshmallow ou validação dedicada antes do controller
```

**Passos de execução**
1. Definir o schema/regra de cada entrada.
2. Implementar um middleware/validador reutilizável.
3. Aplicá-lo antes do controller; controller assume entrada válida.

---

## Padrão 8 — Separar configuração em módulo config
**Anti-pattern alvo:** C2 (secrets), M2 (magic numbers)

**ANTES**
```python
app.config["DEBUG"] = True
# desconto: 0.1 / 0.05 / 0.02 espalhados; port 5000 fixo
```

**DEPOIS**
```python
# src/config/config.py
import os
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
PORT = int(os.getenv("PORT", "5000"))

# regras de negócio nomeadas
DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
```

**Passos de execução**
1. Reunir flags, portas e limites em `src/config/`.
2. Nomear magic numbers como constantes.
3. Ler valores sensíveis do ambiente.

---

## Padrão 9 — Refatorar para Dependency Injection
**Anti-pattern alvo:** H2 (Acoplamento sem DI)

**ANTES**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db")
    return db_connection
```

**DEPOIS**
```python
# conexão criada uma vez na composition root e injetada
def create_app():
    db = create_connection(config.DATABASE_URL)
    product_model = ProductModel(db)              # injeta db
    product_controller = ProductController(product_model)  # injeta model
    ...
    return app
```

**Passos de execução**
1. Remover singletons/globais.
2. Criar a conexão/serviços em um único ponto (factory).
3. Passar as dependências por construtor/parâmetro.

---

## Padrão 10 — Atualizar API deprecated (bodyParser, etc.)
**Anti-pattern alvo:** API deprecated

**ANTES**
```js
const bodyParser = require('body-parser');
app.use(bodyParser.json());                  // deprecado no Express 4.16+
```

**DEPOIS**
```js
app.use(express.json());                     // embutido no Express 4.16+
app.use(express.urlencoded({ extended: true }));
```
Outros exemplos: `new Buffer(x)` → `Buffer.from(x)`; `datetime.utcnow()` →
`datetime.now(timezone.utc)`; `Model.query.get(id)` → `db.session.get(Model, id)`.

**Passos de execução**
1. Grepar pelas APIs deprecated do catálogo (seção "APIs deprecated").
2. Substituir pela API atual equivalente.
3. Remover dependências que se tornaram desnecessárias (ex.: `body-parser` do `package.json`).

---

## Ordem recomendada de aplicação
1. Padrão 3 e 8 (config/segredos) — base segura.
2. Padrão 4 (routers) e 1 (models) — esqueleto de camadas.
3. Padrão 2 e 9 (services/DI) — mover regra de negócio.
4. Padrão 5 e 7 (error handling/validação) — robustez.
5. Padrão 6 e 10 (N+1/deprecated) — performance e modernização.
Após cada grupo, validar que a aplicação sobe e os endpoints respondem.
