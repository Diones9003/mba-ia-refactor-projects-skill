# Skill: Refatoração Arquitetural para MVC
**Comando:** `/refactor-arch`
**Versão:** 1.0.0
**Tecnologias suportadas:** Python/Flask, Node.js/Express (agnóstico)

---

## Objetivo

Esta skill instrui o agente Claude Code a **auditar** e **refatorar** projetos backend legados,
migrando-os de arquiteturas monolíticas / com forte acoplamento para o padrão **MVC (Model-View-Controller)**
em camadas bem definidas.

A skill é **agnóstica de tecnologia**: detecta automaticamente a stack (Python/Flask ou Node.js/Express)
e aplica as heurísticas, o catálogo de anti-patterns e o playbook de refatoração adequados.

A execução acontece em **3 fases sequenciais**, com um **ponto de pausa obrigatório** entre a
auditoria e a refatoração — nenhuma modificação de código pode ocorrer sem confirmação humana explícita.

---

## Arquivos de referência

Estes arquivos ficam nesta mesma pasta (`.claude/skills/refactor-arch/`) e devem ser lidos pelo agente
**no momento indicado de cada fase** — nunca todos de uma vez:

| Arquivo | Fase de uso | Conteúdo |
|---------|-------------|----------|
| `01-project-analysis.md`     | Fase 1 | Heurísticas de detecção de linguagem, framework, banco, arquitetura e domínio |
| `02-antipatterns-catalog.md` | Fase 2 | Catálogo de anti-patterns por severidade (CRITICAL → LOW) |
| `03-audit-report-template.md`| Fase 2 | Template padronizado do relatório de auditoria |
| `04-mvc-guidelines.md`       | Fase 3 | Estrutura-alvo MVC e responsabilidades de cada camada |
| `05-refactoring-playbook.md` | Fase 3 | Padrões de transformação ANTES → DEPOIS |

---

## FASE 1 — ANÁLISE

**Meta:** entender o projeto antes de julgá-lo.

1. **Ler o guia** `01-project-analysis.md` e aplicar suas heurísticas.
2. Percorrer a raiz do projeto e detectar:
   - **Linguagem** — pelo conteúdo dos arquivos (`def`/`import` → Python; `function`/`require`/`const` → Node.js).
   - **Framework** — `from flask import` → Flask; `require('express')` → Express.
   - **Dependências** — ler `requirements.txt` (Python) ou `package.json` (Node.js).
   - **Banco de dados** — `sqlite3`, `SQLAlchemy`, `mongoose`, `sequelize`, etc.
   - **Domínio da aplicação** — inferido dos nomes de rotas, tabelas e entidades (ex.: `produtos`, `pedidos` → e-commerce).
   - **Número de arquivos de código** e **linhas totais**.
   - **Tabelas de banco** encontradas em `CREATE TABLE` ou em models declarativos.
3. **Imprimir um resumo formatado em caixa ASCII**, por exemplo:

```
╔══════════════════════════════════════════════════════════╗
║                  ANÁLISE DO PROJETO                        ║
╠══════════════════════════════════════════════════════════╣
║ Linguagem   : Python 3                                     ║
║ Framework   : Flask 3.1.1                                  ║
║ Banco       : SQLite (sqlite3, acesso manual via cursor)   ║
║ Arquitetura : Monolítica (models = DAO, sem camada service)║
║ Domínio     : E-commerce (produtos, usuários, pedidos)     ║
║ Arquivos    : 4 (.py)                                       ║
║ Linhas      : ~780                                          ║
║ Tabelas     : produtos, usuarios, pedidos, itens_pedido    ║
╚══════════════════════════════════════════════════════════╝
```

> **Não modifique nenhum arquivo nesta fase.** É apenas leitura e diagnóstico.

---

## FASE 2 — AUDITORIA

**Meta:** cruzar o código-fonte contra o catálogo de anti-patterns e gerar um relatório acionável.

1. **Ler os arquivos de referência** `01-project-analysis.md`, `02-antipatterns-catalog.md` e `03-audit-report-template.md`.
2. Reler cada arquivo de código-fonte do projeto e, para cada trecho suspeito, casar com um anti-pattern do catálogo.
3. Registrar cada ocorrência como um **finding** contendo:
   - **Severidade** — `CRITICAL`, `HIGH`, `MEDIUM` ou `LOW`.
   - **Nome** do anti-pattern.
   - **Arquivo:linha** exatos.
   - **Descrição** — o que foi encontrado.
   - **Impacto** — por que é um problema (segurança, manutenção, performance...).
   - **Recomendação** — como corrigir.
4. Gerar o **relatório completo** seguindo `03-audit-report-template.md`, com os findings
   **ordenados por severidade decrescente** (CRITICAL → HIGH → MEDIUM → LOW).
5. **PAUSAR** e apresentar a pergunta de confirmação:

```
Prosseguir com a refatoração? [s/n]
```

> **REGRA CRÍTICA:** nenhuma modificação de arquivo pode ocorrer antes de o usuário responder `s`.
> Se a resposta for `n` (ou qualquer coisa diferente de `s`), encerrar a skill entregando apenas o relatório.

---

## FASE 3 — REFATORAÇÃO

**Meta:** reestruturar o projeto para MVC preservando o comportamento externo (os endpoints originais).

**Só executar após confirmação `s` na Fase 2.**

1. **Ler os arquivos de referência** `04-mvc-guidelines.md` e `05-refactoring-playbook.md`.
2. Criar a estrutura de diretórios alvo:
   ```
   src/config/       → configuração e variáveis de ambiente
   src/models/       → acesso a dados e validação de domínio
   src/views/        → serialização de respostas / roteamento (routes)
   src/controllers/  → orquestração do fluxo de cada endpoint
   src/middlewares/  → error handling, autenticação, validação transversal
   ```
3. **Mover / criar arquivos** aplicando os padrões do playbook (`05-refactoring-playbook.md`):
   extrair models de God Classes, mover lógica de negócio dos controllers para services/models,
   remover credenciais hardcoded para `.env`, separar rotas, centralizar error handling, eliminar
   SQL dentro de loop, adicionar validação de entrada, separar configuração, aplicar injeção de
   dependência e atualizar APIs deprecated.
4. **Validar** que a aplicação ainda funciona:
   - A aplicação **inicia sem erros** (`python app.py` / `npm start`).
   - Os **endpoints originais continuam respondendo** com os mesmos contratos (usar o `api.http`/rotas conhecidas).
5. **Imprimir o resumo final** contendo:
   - A **nova estrutura de diretórios** (árvore).
   - Um **checklist de validação**, por exemplo:

```
RESUMO DA REFATORAÇÃO
─────────────────────
Estrutura nova:
  src/
  ├── config/        (config.py + .env)
  ├── models/        (product.py, user.py, order.py)
  ├── views/         (product_routes.py, user_routes.py, order_routes.py)
  ├── controllers/   (product_controller.py, ...)
  └── middlewares/   (error_handler.py)

Checklist de validação:
  [✓] Aplicação inicia sem erros
  [✓] Credenciais movidas para .env
  [✓] Lógica de negócio fora dos controllers
  [✓] SQL parametrizado (sem concatenação)
  [✓] Endpoints originais respondendo
  [✓] Error handling centralizado
```

---

## Princípios gerais

- **Nunca** modificar código na Fase 1 ou Fase 2.
- **Sempre** pausar e pedir confirmação antes da Fase 3.
- Preservar o **contrato externo** dos endpoints (mesmos paths, métodos e formatos de resposta).
- Preferir mudanças **incrementais e verificáveis** a reescritas totais.
- Registrar tudo: cada finding rastreável a `arquivo:linha`.
