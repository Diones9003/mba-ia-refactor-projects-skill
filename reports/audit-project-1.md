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
| CRITICAL   | 3          |
| HIGH       | 2          |
| MEDIUM     | 3          |
| LOW        | 2          |
| **TOTAL**  | **10**     |

## Findings
> Ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW).

### [CRITICAL] SQL Injection por concatenação de strings
- **File:** `models.py:28`, `models.py:47-50`, `models.py:110`, `models.py:289-297`
- **Description:** Praticamente todas as queries são montadas concatenando strings com valores vindos do usuário. Ex.: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` (linha 28) e o login `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (linha 110).
- **Impact:** Injeção de SQL trivial — bypass de autenticação, leitura/alteração/exclusão de qualquer dado. Falha de segurança gravíssima.
- **Recommendation:** Usar sempre queries parametrizadas (`?` placeholders) ou um ORM. Ver playbook — a camada Model deve encapsular acesso a dados com parâmetros.

### [CRITICAL] Hardcoded Secret / SECRET_KEY exposta
- **File:** `app.py:7`, `controllers.py:289`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` fixa no código; além disso o endpoint `/health` devolve a própria secret key no JSON (`"secret_key": "minha-chave-super-secreta-123"`, controllers.py:289).
- **Impact:** Segredo versionado e ainda exposto publicamente via API — comprometimento total de sessões/assinaturas.
- **Recommendation:** Mover para `.env` (`os.getenv`), nunca versionar, e remover o segredo do payload do health check. Ver playbook padrão 3.

### [CRITICAL] Endpoint de execução de SQL arbitrário e reset de banco sem auth
- **File:** `app.py:59-78` (`/admin/query`), `app.py:47-57` (`/admin/reset-db`)
- **Description:** `/admin/query` executa qualquer SQL recebido no corpo (`cursor.execute(query)`) e `/admin/reset-db` apaga todas as tabelas — ambos **sem autenticação**.
- **Impact:** Qualquer pessoa pode executar comandos arbitrários no banco ou destruir todos os dados. RCE-equivalente no banco.
- **Recommendation:** Remover esses endpoints ou protegê-los com autenticação/autorização forte e allowlist. Nunca aceitar SQL cru do cliente.

### [HIGH] Lógica de negócio e side-effects no Controller
- **File:** `controllers.py:208-210`, `controllers.py:247-250`
- **Description:** O controller de pedido simula envio de e-mail/SMS/push com `print(...)` (linhas 208-210) e o de status faz notificações inline (247-250). Regra de negócio/integração dentro do handler HTTP.
- **Impact:** Regra não reutilizável nem testável fora do HTTP; controller acumula responsabilidades.
- **Recommendation:** Extrair para um Service de pedidos/notificação; controller apenas orquestra. Ver playbook padrão 2.

### [HIGH] SQL dentro de loop (N+1 queries)
- **File:** `models.py:187-199` (`get_pedidos_usuario`), `models.py:219-231` (`get_todos_pedidos`)
- **Description:** Para cada pedido executa uma query de itens e, para cada item, outra query de produto (`cursor2`/`cursor3` dentro de loops aninhados).
- **Impact:** Número de queries cresce com pedidos×itens; performance degrada severamente com volume.
- **Recommendation:** Substituir por um JOIN entre `pedidos`, `itens_pedido` e `produtos` e agrupar em memória. Ver playbook padrão 6.

### [MEDIUM] Senhas armazenadas e trafegadas em texto puro
- **File:** `models.py:122-131` (`criar_usuario`), `models.py:80-86` (`get_todos_usuarios` retorna `senha`), `database.py:76-78`
- **Description:** Senhas são inseridas sem hash (`INSERT ... senha ...`) e retornadas nas respostas de listagem de usuários; seed cria `admin123`/`123456` em claro.
- **Impact:** Vazamento de credenciais no banco e nas respostas da API.
- **Recommendation:** Aplicar hash forte (bcrypt/argon2) no Model e nunca serializar o campo `senha`. Ver guidelines de Model.

### [MEDIUM] Magic Numbers nas regras de desconto
- **File:** `models.py:256-262`
- **Description:** Faixas de desconto com literais mágicos: `if faturamento > 10000: desconto = faturamento * 0.1` etc., sem constantes nomeadas.
- **Impact:** Regra de negócio obscura e difícil de alterar/testar.
- **Recommendation:** Extrair para constantes/config (`DISCOUNT_TIERS`). Ver playbook padrão 8.

### [MEDIUM] Validação duplicada e espalhada nos controllers
- **File:** `controllers.py:28-54` (criar_produto), `controllers.py:72-90` (atualizar_produto)
- **Description:** Blocos quase idênticos de validação (`if "nome" not in dados`, faixas de preço/estoque, categorias) repetidos entre criar e atualizar produto.
- **Impact:** Duplicação; alterações precisam ser feitas em vários pontos, com risco de divergência.
- **Recommendation:** Centralizar em validador/schema reutilizável (middleware) antes do controller. Ver playbook padrões 5 e 7.

### [LOW] `DEBUG=True` e servidor exposto em 0.0.0.0
- **File:** `app.py:8`, `app.py:88`
- **Description:** `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` — configuração de produção insegura embutida no código.
- **Impact:** Debugger/PIN expostos e stack traces detalhados vazando para clientes.
- **Recommendation:** Controlar `DEBUG` via variável de ambiente e desabilitar em produção. Ver playbook padrão 8.

### [LOW] Comentários/mensagens enganosos e prints de depuração
- **File:** `controllers.py:8`, `controllers.py:179`, `app.py:56`
- **Description:** Uso de `print` como "log" (`"Listando N produtos"`, `"Login bem-sucedido: " + email`) e mensagens em maiúsculas simulando eventos; `/health` afirma `"ambiente": "producao"` num app com SQLite local e DEBUG ligado.
- **Impact:** Ruído, vazamento de dados sensíveis em logs (email de login) e informação enganosa.
- **Recommendation:** Usar logging estruturado com níveis e remover mensagens enganosas.

## Rodapé
- **Total de findings:** 10
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
