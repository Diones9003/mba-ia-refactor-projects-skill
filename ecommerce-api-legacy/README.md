# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, **refatorada para MVC em camadas** pela skill
`refactor-arch`. Os três endpoints originais foram preservados; a auditoria que originou a
refatoração está em `../reports/audit-project-2.md`.

## Como rodar

```bash
npm install
cp .env.example .env      # preencha PAYMENT_GATEWAY_KEY
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória (`DATABASE_PATH=:memory:`)
e carrega seeds automaticamente no boot. Exemplos de requisições estão em `api.http`.

> A aplicação falha no boot se `PAYMENT_GATEWAY_KEY` não estiver definida — segredos vêm do
> ambiente, nunca do código.

## Validação de contrato

```bash
npm run validate
```

Sobe a aplicação em porta efêmera com banco isolado e confere status codes, `Content-Type`, payloads
e as mensagens de erro herdadas do código original (20 checks).

## Estrutura

```
src/
├── app.js                  composition root: injeta dependências, monta routers e middlewares
├── errors.js               erros de domínio (AppError, ValidationError, NotFoundError, ...)
├── config/
│   ├── index.js            leitura de process.env (dotenv) com fail fast em segredos
│   └── constants.js        status de pagamento, parâmetros de hash, mensagens
├── database/
│   ├── connection.js       adapter Promise sobre sqlite3 + transaction()
│   └── schema.js           DDL (com foreign keys) e seeds
├── models/                 acesso a dados por entidade, com `db` injetado
│   ├── userModel.js  courseModel.js  enrollmentModel.js
│   ├── paymentModel.js  auditLogModel.js
│   └── reportModel.js      query única com JOINs (elimina o N+1 do relatório)
├── services/               regra de negócio
│   ├── checkoutService.js  reportService.js  userService.js
│   ├── paymentGateway.js   adapter do gateway (decide PAID/DENIED)
│   ├── passwordHasher.js   scrypt + salt
│   └── cacheService.js     cache com limite de entradas
├── controllers/            orquestração de cada endpoint
│   ├── checkoutController.js  reportController.js  userController.js
├── views/                  roteamento + serialização
│   ├── checkoutRoutes.js  reportRoutes.js  userRoutes.js
│   └── serializers.js
└── middlewares/
    ├── errorHandler.js     único ponto que traduz erro → resposta HTTP
    ├── validate.js         validação de body/params por schema
    ├── asyncHandler.js     encaminha rejeições ao error handler
    └── notFound.js
```

## Endpoints

| Método | Path | Resposta |
|--------|------|----------|
| POST   | `/api/checkout` | `200 {"msg":"Sucesso","enrollment_id":N}` · `400 Bad Request` · `400 Pagamento recusado` · `404 Curso não encontrado` |
| GET    | `/api/admin/financial-report` | `200 [{"course","revenue","students":[{"student","paid"}]}]` |
| DELETE | `/api/users/:id` | `200` texto · `400 Bad Request` · `404 Usuário não encontrado` |

Os nomes dos campos do checkout (`usr`, `eml`, `pwd`, `c_id`, `card`) foram mantidos por contrato.

## Mudanças de comportamento intencionais

A refatoração preserva paths, métodos e payloads de sucesso. Estas exceções corrigem bugs apontados
na auditoria:

- `DELETE /api/users/:id` remove matrículas e pagamentos na mesma transação (antes deixava órfãos) e
  responde `404` para usuário inexistente e `400` para id não numérico (antes respondia sempre `200`).
- Falha de banco na busca do curso retorna `500` em vez de `404`.
- Falha ao gravar o log de auditoria aborta a transação do checkout em vez de responder sucesso.
- Entradas malformadas (e-mail sem formato válido, `c_id` não numérico, cartão fora de 13–19 dígitos)
  retornam `400 Bad Request`.
- A ordem do relatório financeiro é determinística (por id do curso); antes dependia de qual callback
  respondia primeiro.
- Contas criadas sem `pwd` recebem senha aleatória em vez de uma senha padrão fixa.
