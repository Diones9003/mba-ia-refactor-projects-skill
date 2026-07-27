# 01 — Guia de Análise de Projeto

Este guia reúne as heurísticas que o agente deve aplicar na **Fase 1 (Análise)** para entender
qualquer projeto backend antes de auditá-lo ou refatorá-lo. É **agnóstico de tecnologia**: cada
seção lista sinais para Python/Flask e para Node.js/Express.

O objetivo desta fase é produzir um diagnóstico factual — **sem julgamentos e sem modificações** —
que alimenta as fases seguintes.

---

## 1. Detecção de linguagem

A linguagem é inferida **pelo conteúdo dos arquivos**, não apenas pela extensão (que pode enganar
em monorepos ou arquivos mal nomeados).

### Sinais de Python
- Palavra-chave `def ` para funções e `class ` para classes.
- Imports no estilo `import os` / `from flask import Flask`.
- Indentação significativa (blocos por espaços, sem chaves).
- Ausência de `;` no fim das linhas.
- Arquivos `.py`, `requirements.txt`, `Pipfile`, `pyproject.toml`.

### Sinais de Node.js / JavaScript
- `const` / `let` / `var` para declaração de variáveis.
- `function nome() {}` ou arrow functions `() => {}`.
- `require('modulo')` (CommonJS) ou `import x from 'modulo'` (ESM).
- Uso de `;` e chaves `{}` para blocos.
- Arquivos `.js`/`.mjs`/`.ts`, `package.json`, `package-lock.json`.

### Procedimento
1. Listar os arquivos de código da raiz e subpastas (ignorar `node_modules/`, `__pycache__/`, `.git/`).
2. Abrir 2–3 arquivos representativos e procurar os sinais acima.
3. Confirmar a versão pela dependência declarada (ver seção 3).

---

## 2. Detecção de framework

O framework define onde estão as rotas, o ciclo de request/response e o ponto de entrada.

| Framework | Sinal principal | Sinais secundários |
|-----------|-----------------|--------------------|
| **Flask** (Python) | `from flask import Flask` | `app = Flask(__name__)`, `@app.route(...)`, `app.add_url_rule(...)`, `Blueprint` |
| **FastAPI** (Python) | `from fastapi import FastAPI` | `@app.get`, `@app.post`, `APIRouter` |
| **Django** (Python) | `from django` | `urls.py`, `settings.py`, `models.Model` |
| **Express** (Node) | `require('express')` | `const app = express()`, `app.get/post/put/delete`, `app.use(...)`, `app.listen(...)` |
| **NestJS** (Node) | `@nestjs/common` | decorators `@Controller`, `@Injectable` |

### Procedimento
1. Localizar o arquivo de entrada (`app.py`, `main.py`, `src/app.js`, `index.js`).
2. Procurar a instanciação da aplicação e o registro de rotas.
3. Anotar **como** as rotas são registradas — isso indica o grau de organização
   (ex.: `app.add_url_rule` centralizado, decorators espalhados, Blueprints, um "Manager" que registra tudo).

---

## 3. Detecção de banco de dados

O banco e a forma de acesso determinam boa parte dos anti-patterns (SQL injection, N+1, etc.).

### Python
- `import sqlite3` + `sqlite3.connect(...)` → **SQLite com acesso manual via cursor** (alto risco de SQL string).
- `from flask_sqlalchemy import SQLAlchemy` / `db = SQLAlchemy()` → **ORM SQLAlchemy**.
- `import psycopg2` → PostgreSQL; `import pymysql`/`MySQLdb` → MySQL; `pymongo` → MongoDB.

### Node.js
- `require('sqlite3')` → SQLite (frequentemente com SQL manual em callbacks).
- `require('mongoose')` → MongoDB via ODM.
- `require('sequelize')` / `require('typeorm')` / `require('prisma')` → ORMs relacionais.
- `require('pg')` / `require('mysql2')` → drivers relacionais diretos.

### Procedimento
1. Identificar a biblioteca de acesso.
2. Verificar se as queries são **parametrizadas** (`?`, `:param`) ou **concatenadas** (string + variável) — este é um achado crítico da auditoria.
3. Verificar se a conexão é **global/singleton** ou criada por request.

---

## 4. Detecção de tabelas / entidades

Mapear o modelo de dados ajuda a inferir o domínio e a planejar os Models na refatoração.

- **SQL manual:** procurar `CREATE TABLE <nome>` e listar as colunas.
- **ORM declarativo (SQLAlchemy):** procurar classes que herdam de `db.Model` e o atributo `__tablename__`.
- **Mongoose:** procurar `new Schema({...})` e `mongoose.model('Nome', schema)`.
- **Sequelize:** procurar `sequelize.define('nome', {...})`.

Para cada entidade, anotar: nome, campos, relacionamentos (chaves estrangeiras / `db.relationship` / `references`).

---

## 5. Mapeamento da arquitetura atual

Classificar o projeto em um dos padrões abaixo (ou combinação):

- **Monolítica de arquivo único** — toda a lógica em um `app.py`/`app.js`.
- **Monolítica em camadas fracas** — separação por arquivos (`models.py`, `controllers.py`) mas com
  responsabilidades vazando (ex.: SQL no model chamado de "model" que na verdade é DAO, lógica de
  negócio no controller, validação espalhada).
- **God Class / God Manager** — uma única classe concentra rotas, acesso a dados, regras de negócio
  e integrações (sinal: classe com centenas de linhas, muitos métodos e `this.db` por toda parte).
- **MVC parcial** — já existe divisão em `models/`, `routes/`, `services/`, mas com camadas
  inconsistentes (regra de negócio duplicada nas rotas, serialização manual repetida).
- **MVC / Clean** — camadas bem separadas (alvo da refatoração).

### Sinais úteis
- Serialização de resposta repetida em cada handler → falta de camada de View/serializer.
- Blocos `try/except` genéricos em cada função → falta de error handling centralizado.
- Configuração e segredos no topo do arquivo de entrada → falta de camada de config.

---

## 6. Identificação do domínio da aplicação

O domínio é inferido pelo **vocabulário** do código:

- **Nomes de rotas:** `/produtos`, `/pedidos`, `/checkout` → e-commerce; `/tasks`, `/categories` → gestão de tarefas; `/courses`, `/enrollments` → educação/LMS.
- **Nomes de tabelas/entidades:** `users`, `courses`, `enrollments`, `payments` → plataforma de cursos.
- **Nomes de funções:** `criar_pedido`, `relatorio_vendas`, `notify_task_overdue`.

Descreva o domínio em uma frase, ex.: *"API de e-commerce com catálogo de produtos, usuários,
pedidos e relatório de vendas"*.

---

## 7. Heurísticas para contar arquivos e linhas de código

O tamanho do projeto contextualiza a severidade dos achados (uma God Class de 500 linhas é pior
que uma de 50).

### Contagem de arquivos
- Listar recursivamente os arquivos de código da linguagem detectada.
- **Ignorar**: `node_modules/`, `__pycache__/`, `.git/`, `dist/`, `build/`, `venv/`, arquivos gerados e lockfiles.
- Separar por tipo: código de aplicação vs. testes vs. configuração.

### Contagem de linhas (LOC)
- Comandos úteis (apenas leitura):
  - Python: `find . -name "*.py" -not -path "*/venv/*" | xargs wc -l`
  - Node.js: `find . -name "*.js" -not -path "*/node_modules/*" | xargs wc -l`
- Distinguir **linhas totais** de **linhas efetivas** (descontando linhas em branco e comentários) quando relevante.
- Sinalizar arquivos individuais muito grandes (> ~250 linhas) como candidatos a God Class/God File.

### Métricas complementares
- Nº de rotas/endpoints (contar handlers ou registros de rota).
- Nº de funções por arquivo (densidade de responsabilidade).
- Maior função do projeto (linhas) — candidata a God Method.

---

## 8. Saída esperada da Fase 1

Ao final, o agente deve produzir o **resumo em caixa ASCII** descrito no `SKILL.md`, contendo:
linguagem, framework, banco, arquitetura atual, domínio, número de arquivos, linhas e tabelas.
Esse resumo é o insumo direto do cabeçalho do relatório de auditoria (Fase 2).
