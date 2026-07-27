# 04 — Guidelines de Arquitetura MVC (Alvo)

Guia de referência da **Fase 3 (Refatoração)**. Define a **estrutura-alvo** e as
**responsabilidades de cada camada** para Python/Flask e Node.js/Express. O objetivo é migrar de um
monólito acoplado para um MVC em camadas, preservando o contrato externo dos endpoints.

---

## 1. Estrutura de diretórios obrigatória

A skill adota o prefixo `src/` como raiz de código e as seguintes camadas:

```
src/
├── config/        # configuração e variáveis de ambiente
├── models/        # acesso a dados + validação de domínio (Model/Repository)
├── views/         # roteamento + serialização de respostas (routes/serializers)
├── controllers/   # orquestração do fluxo de cada endpoint
└── middlewares/   # error handling, autenticação, validação transversal
```

> Observação sobre "View" em APIs: em uma API REST não há template HTML; a camada **View** é
> representada pelas **rotas + serialização da resposta** (transformar objetos de domínio em JSON).

### Python / Flask
```
src/
├── config/
│   └── config.py            # lê .env via os.getenv; classes Config/DevConfig/ProdConfig
├── models/
│   ├── __init__.py
│   ├── product.py           # classe/DAO Produto
│   ├── user.py
│   └── order.py
├── views/                   # Blueprints Flask (roteamento + serialização)
│   ├── __init__.py
│   ├── product_routes.py
│   ├── user_routes.py
│   └── order_routes.py
├── controllers/
│   ├── product_controller.py
│   ├── user_controller.py
│   └── order_controller.py
├── middlewares/
│   └── error_handler.py     # @app.errorhandler centralizado
└── app.py                   # factory create_app(), registra blueprints e middlewares
```

### Node.js / Express
```
src/
├── config/
│   └── index.js             # lê process.env via dotenv
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   └── paymentModel.js
├── views/                   # routers Express (roteamento + serialização)
│   ├── userRoutes.js
│   ├── checkoutRoutes.js
│   └── reportRoutes.js
├── controllers/
│   ├── userController.js
│   ├── checkoutController.js
│   └── reportController.js
├── middlewares/
│   ├── errorHandler.js
│   └── validate.js
├── services/                # regras de negócio reutilizáveis (opcional, recomendado)
│   └── paymentService.js
└── app.js                   # cria app, monta routers e middlewares, app.listen
```

---

## 2. Responsabilidades de cada camada

### Models (acesso a dados + validação de domínio)
- Encapsulam **todo** o acesso ao banco (queries, ORM). Nenhuma outra camada fala SQL diretamente.
- Expõem métodos de domínio (`Product.find_all()`, `Order.create(...)`).
- Contêm **validação de invariantes de domínio** (ex.: preço não negativo, status válido).
- **Não** conhecem `request`/`response` nem detalhes de HTTP.

### Views / Routes (roteamento + serialização)
- Declaram os **paths, métodos HTTP** e associam cada rota ao seu controller.
- Fazem a **serialização** da resposta (objeto → JSON) e definem o status code.
- **Não** contêm regra de negócio nem SQL.

### Controllers (orquestração do fluxo)
- Recebem a request já roteada, extraem/validam a entrada (delegando ao middleware de validação quando possível).
- **Orquestram**: chamam Services/Models, tratam o resultado e devolvem para a View serializar.
- **Não** executam SQL diretamente nem implementam a regra de negócio detalhada — apenas o fluxo.

### Middlewares (transversais)
- **Error handling centralizado**: um único ponto que captura exceções e formata a resposta de erro.
- **Autenticação/autorização**, **validação de schema**, **logging** e CORS.
- Aplicados globalmente ou por grupo de rotas.

### Services (opcional, recomendado para regra de negócio rica)
- Concentram regras de negócio que envolvem múltiplos models ou integrações (pagamento, notificação, relatórios).
- Reutilizáveis e testáveis isoladamente.

---

## 3. Naming conventions

### Arquivos
- **Python:** `snake_case.py` — `product_controller.py`, `user_routes.py`, `order.py`.
- **Node.js:** `camelCase.js` — `userController.js`, `checkoutRoutes.js` (ou `kebab-case.js`, mas seja consistente).
- Sufixos por camada: `_controller`/`Controller`, `_routes`/`Routes`, `_service`/`Service`, model no singular (`user.py`/`userModel.js`).

### Funções e classes
- **Classes:** `PascalCase` (`ProductController`, `OrderService`).
- **Funções/métodos:** `snake_case` (Python) / `camelCase` (Node).
- Nomes **descritivos e no idioma consistente do projeto**; funções de rota nomeadas pela ação (`create_product`, `listOrders`).
- Evitar abreviações crípticas (`u`, `e`, `cc`) — ver anti-pattern L1.

---

## 4. Injeção de dependência (DI)

- Componentes **recebem** suas dependências (conexão de banco, services) via **construtor ou parâmetro**,
  em vez de instanciá-las internamente.
- Uma única fábrica/composition root monta o grafo de dependências no start da aplicação
  (`create_app()` no Flask, `app.js` no Express).
- Benefício: permite **mocks** em testes e troca de implementação sem editar as classes consumidoras.

```python
# em vez de conexão global:
class ProductModel:
    def __init__(self, db):      # db injetado
        self.db = db
```
```js
class CheckoutController {
  constructor(paymentService, enrollmentModel) {   // injetados
    this.paymentService = paymentService;
    this.enrollmentModel = enrollmentModel;
  }
}
```

---

## 5. Configuração e variáveis de ambiente

- **Nenhum segredo no código.** Centralizar em `src/config/` lendo de variáveis de ambiente.
- Python: `python-dotenv` + `os.getenv("SECRET_KEY")`; Node: `dotenv` + `process.env.SECRET_KEY`.
- Versionar apenas um **`.env.example`** com as chaves (sem valores reais); adicionar `.env` ao `.gitignore`.
- Separar perfis (`development`, `production`) e nunca deixar `DEBUG=True` em produção.

```python
# src/config/config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

---

## 6. Error handling centralizado

- Substituir os `try/except`/`try/catch` genéricos repetidos em cada handler por **um middleware único**.
- O handler central: registra o erro (log), mapeia o tipo de exceção para um status code e devolve um
  corpo de erro **padronizado** (`{ "error": "...", "code": ... }`).
- Controllers passam a lançar exceções de domínio (ou repassá-las), sem formatar resposta de erro.

```python
# src/middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle(e):
        app.logger.exception(e)
        return {"error": "Erro interno", "sucesso": False}, 500
```
```js
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).json({ error: err.message || "Erro interno" });
};
// app.use(errorHandler)  → registrado por último
```

---

## 7. Regras de preservação de comportamento

- **Mesmos paths e métodos** dos endpoints originais.
- **Mesmo formato de resposta** (chaves JSON, status codes) — a refatoração é interna.
- Validar após a refatoração: aplicação inicia e endpoints respondem igual (Fase 3, passo de validação).
