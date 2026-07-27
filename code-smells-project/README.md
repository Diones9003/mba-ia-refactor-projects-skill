# code-smells-project

API de E-commerce em Python/Flask, refatorada de monólito acoplado para **MVC em camadas**
pela skill `refactor-arch`. O contrato dos endpoints originais foi preservado.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # e preencha SECRET_KEY
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (host/porta configuráveis no `.env`).
O banco SQLite (`loja.db`) é criado no primeiro boot, já com produtos e usuários de exemplo.

Gerar uma `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Estrutura

```
app.py                    # ponto de entrada (wiring + servidor de dev)
src/
├── app.py                # factory create_app() — composition root da injeção de dependência
├── errors.py             # exceções de domínio (ValidationError, NotFoundError, ...)
├── config/               # configuração via .env + constantes de domínio
├── database/             # criação de conexão (por request) + schema/seed
├── models/               # acesso a dados, 100% parametrizado
├── services/             # regras de negócio (pedidos, relatório, notificações)
├── controllers/          # orquestração de cada endpoint
├── views/                # blueprints (rotas) + serialização das respostas
└── middlewares/          # error handling centralizado, validação, logging
scripts/
├── reset_db.py           # reset do banco (substitui o antigo POST /admin/reset-db)
└── validate_contracts.py # 68 verificações de contrato dos endpoints
```

## Scripts

```bash
PYTHONPATH=. python -m scripts.validate_contracts   # valida os endpoints
PYTHONPATH=. python -m scripts.reset_db             # apaga e repopula o banco
PYTHONPATH=. python -m scripts.reset_db --sim       # sem confirmação interativa
```

## Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/` | Índice da API |
| GET | `/health` | Health check + contagens |
| GET | `/produtos` | Lista produtos |
| GET | `/produtos/busca` | Busca por `q`, `categoria`, `preco_min`, `preco_max` |
| GET | `/produtos/<id>` | Busca produto por ID |
| POST | `/produtos` | Cria produto |
| PUT | `/produtos/<id>` | Atualiza produto |
| DELETE | `/produtos/<id>` | Remove produto |
| GET | `/usuarios` | Lista usuários (sem senha) |
| GET | `/usuarios/<id>` | Busca usuário por ID |
| POST | `/usuarios` | Cria usuário |
| POST | `/login` | Autentica (senha com hash) |
| POST | `/pedidos` | Cria pedido (transacional) |
| GET | `/pedidos` | Lista todos os pedidos |
| GET | `/pedidos/usuario/<id>` | Pedidos de um usuário |
| PUT | `/pedidos/<id>/status` | Altera status do pedido |
| GET | `/relatorios/vendas` | Relatório de vendas |

### Endpoints removidos

`POST /admin/query` e `POST /admin/reset-db` foram retirados — executavam SQL arbitrário e
apagavam o banco sem qualquer autenticação. O reset virou `scripts/reset_db.py`.

## Configuração

Todas as variáveis estão documentadas em `.env.example`. O `.env` não é versionado.
Sem `SECRET_KEY` definida, a aplicação só inicia com `DEBUG=true` (usando uma chave de
desenvolvimento explicitamente insegura); fora disso o boot falha com erro claro.
