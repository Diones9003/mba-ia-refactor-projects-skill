# Relatório de Auditoria — task-manager-api

## Cabeçalho
- **Projeto:** `task-manager-api` (Task Manager API)
- **Stack:** Python 3 / Flask 3.0.0 (+ flask-sqlalchemy 3.1.1, flask-cors, marshmallow) / SQLite via ORM SQLAlchemy
- **Arquivos analisados:** `app.py`, `database.py`, `models/{user,task,category}.py`, `routes/{task,user,report}_routes.py`, `services/notification_service.py`, `utils/helpers.py`
- **Linhas de código:** ~700 (routes ~730 no total, models ~120, service 48, helpers 116)
- **Domínio:** Gestão de tarefas — usuários, tarefas, categorias, relatórios e notificações
- **Data da auditoria:** 2026-07-27

> Projeto mais organizado que os demais: já possui separação em `models/`, `routes/`, `services/`, `utils/` (MVC parcial). Os achados são de refinamento arquitetural e segurança pontual.

## Summary (contagem por severidade)
| Severidade | Quantidade |
|------------|------------|
| CRITICAL   | 0          |
| HIGH       | 2          |
| MEDIUM     | 3          |
| LOW        | 2          |
| **TOTAL**  | **7**      |

## Findings
> Ordenados por severidade decrescente (HIGH → MEDIUM → LOW).

### [HIGH] Hash de senha fraco (MD5) e secret key hardcoded
- **File:** `models/user.py:29`, `models/user.py:32`, `app.py:13`
- **Description:** `set_password` usa `hashlib.md5(pwd.encode()).hexdigest()` (linha 29) e `check_password` compara MD5 (linha 32); a `SECRET_KEY = 'super-secret-key-123'` está fixa em `app.py:13`. O `NotificationService` também traz `email_password = 'senha123'` (services/notification_service.py:10).
- **Impact:** MD5 é quebrável (rainbow tables, sem salt); secret e senha de e-mail versionadas comprometem segurança.
- **Recommendation:** Usar bcrypt/argon2 com salt; mover secrets para `.env`. Ver playbook padrão 3 e anti-pattern C2.

### [HIGH] Lógica de negócio e serialização duplicadas nas rotas (N+1 incluso)
- **File:** `routes/task_routes.py:16-59`, `routes/report_routes.py:53-68`, `routes/user_routes.py:159-181`
- **Description:** O cálculo de "overdue" e a montagem manual do dicionário da task estão duplicados em `get_tasks`, `get_task`, `get_user_tasks` e stats; além disso `get_tasks` faz `User.query.get`/`Category.query.get` dentro do loop (linhas 42 e 51) e o summary consulta tasks por usuário dentro de `for u in users` (report_routes.py:56) — padrão N+1.
- **Impact:** Duplicação (DRY) e queries desnecessárias por item; manutenção arriscada e performance degradada.
- **Recommendation:** Centralizar serialização em `Task.to_dict`/serializer e mover a regra de negócio para um Service; usar joins/eager loading. Ver playbook padrões 2, 5 e 6.

### [MEDIUM] `to_dict` do usuário expõe a senha
- **File:** `models/user.py:16-25`
- **Description:** `User.to_dict()` inclui `'password': self.password` (linha 21), e esse dict é retornado em endpoints como `get_user`, `create_user` e `login` (user_routes.py:33, 85, 209).
- **Impact:** Hash de senha vaza nas respostas da API.
- **Recommendation:** Remover o campo `password` da serialização (criar `public_dict`). Ver guidelines de camada View/Model.

### [MEDIUM] Validação de entrada dispersa e não reutilizada
- **File:** `routes/task_routes.py:88-144`, `routes/user_routes.py:54-72`, `utils/helpers.py:57-108`
- **Description:** As rotas repetem validações inline (título 3-200, status válido, prioridade 1-5, regex de e-mail) enquanto existe `process_task_data` em `utils/helpers.py` que faz exatamente isso — mas **não é usado** pelas rotas.
- **Impact:** Duplicação, inconsistência entre criar/atualizar e código morto no helper.
- **Recommendation:** Adotar validação única via schema (marshmallow, já no requirements) ou o helper existente, aplicada como middleware/decorator. Ver playbook padrão 7.

### [MEDIUM] `except` genérico/silencioso mascarando erros
- **File:** `routes/task_routes.py:62-63`, `routes/user_routes.py:130-132`, `routes/report_routes.py:186-188`
- **Description:** Vários blocos usam `except:` nu (bare except) retornando 500 genérico sem logar a causa (ex.: `get_tasks` linhas 62-63; vários `except:` em update/delete).
- **Impact:** Erros reais ficam invisíveis; difícil diagnosticar em produção.
- **Recommendation:** Capturar exceções específicas e centralizar error handling em middleware com logging. Ver playbook padrão 5.

### [LOW] `if/else` verboso retornando booleano
- **File:** `models/user.py:34-38`, `models/task.py:38-60`
- **Description:** `is_admin` faz `if self.role == 'admin': return True else: return False` (poderia ser `return self.role == 'admin'`); `is_overdue`/`validate_status` em `task.py` têm aninhamentos `if/else` que apenas retornam booleanos.
- **Impact:** Verbosidade desnecessária; legibilidade reduzida.
- **Recommendation:** Retornar diretamente a expressão booleana.

### [LOW] Imports não utilizados e uso de API depreciada
- **File:** `routes/task_routes.py:7`, `app.py:7`, `utils/helpers.py:1-7`, uso de `datetime.utcnow()` em vários arquivos
- **Description:** Imports desnecessários (`import json, os, sys, time` em task_routes; `os, sys, json` em app.py; `math, hashlib, sys` em helpers) e uso disseminado de `datetime.utcnow()`, depreciado no Python 3.12+.
- **Impact:** Ruído, confusão sobre dependências e código que emitirá deprecation warnings.
- **Recommendation:** Remover imports não usados e migrar para `datetime.now(timezone.utc)`. Ver catálogo — APIs deprecated.

## Rodapé
- **Total de findings:** 7
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
