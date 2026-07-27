# 03 — Template do Relatório de Auditoria

Este é o **modelo padronizado** que o agente deve preencher na **Fase 2** e salvar em
`reports/audit-project-N.md`. Copie a estrutura abaixo, substituindo os campos entre `<...>` pelos
valores reais colhidos na análise. Mantenha a formatação Markdown e a ordem das seções.

---

## Estrutura do relatório

```markdown
# Relatório de Auditoria — <Nome do Projeto>

## Cabeçalho
- **Projeto:** <nome do diretório / aplicação>
- **Stack:** <linguagem + versão> / <framework + versão> / <banco>
- **Arquivos analisados:** <lista de arquivos>
- **Linhas de código:** <total aproximado>
- **Domínio:** <descrição em uma frase>
- **Data da auditoria:** <YYYY-MM-DD>

## Summary (contagem por severidade)
| Severidade | Quantidade |
|------------|------------|
| CRITICAL   | <n>        |
| HIGH       | <n>        |
| MEDIUM     | <n>        |
| LOW        | <n>        |
| **TOTAL**  | **<n>**    |

## Findings
> Ordenados por severidade decrescente (CRITICAL → HIGH → MEDIUM → LOW).

### [CRITICAL] <Nome do anti-pattern>
- **File:** `<arquivo>:<linha>`
- **Description:** <o que foi encontrado>
- **Impact:** <por que é um problema>
- **Recommendation:** <como corrigir; referência ao padrão do playbook, se houver>

### [HIGH] <Nome do anti-pattern>
- **File:** `<arquivo>:<linha>`
- **Description:** ...
- **Impact:** ...
- **Recommendation:** ...

### [MEDIUM] <Nome do anti-pattern>
- **File:** `<arquivo>:<linha>`
- **Description:** ...
- **Impact:** ...
- **Recommendation:** ...

### [LOW] <Nome do anti-pattern>
- **File:** `<arquivo>:<linha>`
- **Description:** ...
- **Impact:** ...
- **Recommendation:** ...

## Rodapé
- **Total de findings:** <n>
- **Confirmação necessária:** Prosseguir com a refatoração? [s/n]
```

---

## Regras de preenchimento

1. **Um bloco por finding.** Cada finding é uma subseção `### [SEVERIDADE] Nome`.
2. **Sempre citar `arquivo:linha`** reais. Se o problema cobre um intervalo, use `arquivo:inicio-fim`.
3. **Ordenação obrigatória:** todos os CRITICAL primeiro, depois HIGH, MEDIUM e LOW.
4. **Summary bate com Findings:** a contagem da tabela deve ser igual ao número de blocos de cada severidade.
5. **Recommendation acionável:** referencie o padrão correspondente de `05-refactoring-playbook.md` quando aplicável.
6. **Rodapé sempre presente** com o total e a pergunta de confirmação — a auditoria **não** modifica código.
7. Use marcadores e tabelas Markdown; mantenha os rótulos em inglês (`File`, `Description`, `Impact`,
   `Recommendation`) e o texto descritivo em português, para consistência entre relatórios.
