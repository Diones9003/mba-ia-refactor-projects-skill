"""Validação de contrato dos endpoints.

Exercita os 17 endpoints contra um banco temporário e confere status codes,
chaves do JSON e mensagens de erro — inclusive as mensagens herdadas do código
original, que a refatoração preserva.

Uso:
    PYTHONPATH=. python -m scripts.validate_contracts
"""

import os
import tempfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "chave-de-teste"
os.environ["LOG_LEVEL"] = "WARNING"

from src.app import create_app
from src.config import Config

app = create_app(Config())
c = app.test_client()

falhas, total = [], 0

def check(nome, resp, status_esperado, chaves_esperadas=None, validador=None):
    global total
    total += 1
    corpo = resp.get_json()
    erros = []
    if resp.status_code != status_esperado:
        erros.append(f"status {resp.status_code} != {status_esperado}")
    if chaves_esperadas is not None and set(corpo or {}) != set(chaves_esperadas):
        erros.append(f"chaves {sorted(corpo or {})} != {sorted(chaves_esperadas)}")
    if validador:
        problema = validador(corpo)
        if problema:
            erros.append(problema)
    marca = "ok " if not erros else "FALHA"
    print(f"  [{marca}] {nome}" + ("" if not erros else f"  -> {'; '.join(erros)}"))
    if erros:
        falhas.append(nome)
    return corpo

print("\n== índice e health ==")
check("GET /", c.get("/"), 200, ["mensagem", "versao", "endpoints"])
check("GET /health", c.get("/health"), 200, ["status", "database", "counts", "versao", "ambiente"],
      lambda b: "secret_key vazada!" if "secret_key" in b else ("db_path vazado!" if "db_path" in b else None))

print("\n== produtos ==")
b = check("GET /produtos", c.get("/produtos"), 200, ["dados", "sucesso"],
          lambda b: None if len(b["dados"]) == 10 else f"esperava 10 produtos, veio {len(b['dados'])}")
campos_produto = {"id","nome","descricao","preco","estoque","categoria","ativo","criado_em"}
check("  campos do produto", c.get("/produtos"), 200, None,
      lambda b: None if set(b["dados"][0]) == campos_produto else f"campos {sorted(set(b['dados'][0]) ^ campos_produto)} divergentes")
check("GET /produtos/1", c.get("/produtos/1"), 200, ["dados", "sucesso"])
check("GET /produtos/9999 (404)", c.get("/produtos/9999"), 404, ["erro", "sucesso"],
      lambda b: None if b["erro"] == "Produto não encontrado" else f"msg '{b['erro']}'")
check("GET /produtos/busca?q=mouse", c.get("/produtos/busca?q=mouse"), 200, ["dados","total","sucesso"],
      lambda b: None if b["total"] == 1 else f"total {b['total']} != 1")
check("GET /produtos/busca filtros", c.get("/produtos/busca?categoria=informatica&preco_min=100&preco_max=500"), 200,
      ["dados","total","sucesso"], lambda b: None if b["total"] == 4 else f"total {b['total']} != 4")

novo = check("POST /produtos", c.post("/produtos", json={"nome":"Produto Teste","preco":10.5,"estoque":3,"categoria":"livros"}),
             201, ["dados","sucesso","mensagem"],
             lambda b: None if b["mensagem"]=="Produto criado" and "id" in b["dados"] else "payload divergente")
pid = novo["dados"]["id"]
check("PUT /produtos/<id>", c.put(f"/produtos/{pid}", json={"nome":"Produto Editado","preco":20,"estoque":5,"categoria":"livros"}),
      200, ["sucesso","mensagem"], lambda b: None if b["mensagem"]=="Produto atualizado" else "msg divergente")
check("  update persistido", c.get(f"/produtos/{pid}"), 200, None,
      lambda b: None if b["dados"]["nome"]=="Produto Editado" and b["dados"]["preco"]==20 else "não persistiu")
check("PUT /produtos/9999 (404)", c.put("/produtos/9999", json={"nome":"X","preco":1,"estoque":1}), 404, ["erro","sucesso"])
check("DELETE /produtos/<id>", c.delete(f"/produtos/{pid}"), 200, ["sucesso","mensagem"],
      lambda b: None if b["mensagem"]=="Produto deletado" else "msg divergente")
check("DELETE /produtos/9999 (404)", c.delete("/produtos/9999"), 404, ["erro","sucesso"])

print("\n== validação de produtos (mensagens originais preservadas) ==")
casos = [
    ({}, "Dados inválidos"),
    ({"preco":1,"estoque":1}, "Nome é obrigatório"),
    ({"nome":"Teste","estoque":1}, "Preço é obrigatório"),
    ({"nome":"Teste","preco":1}, "Estoque é obrigatório"),
    ({"nome":"Teste","preco":-1,"estoque":1}, "Preço não pode ser negativo"),
    ({"nome":"Teste","preco":1,"estoque":-1}, "Estoque não pode ser negativo"),
    ({"nome":"A","preco":1,"estoque":1}, "Nome muito curto"),
    ({"nome":"A"*201,"preco":1,"estoque":1}, "Nome muito longo"),
    ({"nome":"Teste","preco":1,"estoque":1,"categoria":"invalida"}, "Categoria inválida. Válidas: ['informatica', 'moveis', 'vestuario', 'geral', 'eletronicos', 'livros']"),
]
for payload, msg in casos:
    check(f"POST /produtos -> '{msg[:38]}'", c.post("/produtos", json=payload), 400, ["erro","sucesso"],
          lambda b, m=msg: None if b["erro"]==m else f"msg '{b['erro']}'")

print("\n== correções de comportamento (antes eram 500) ==")
check("POST /produtos preco string -> 400", c.post("/produtos", json={"nome":"Teste","preco":"10","estoque":1}), 400, ["erro","sucesso"])
check("POST /produtos sem body -> 400", c.post("/produtos"), 400, ["erro","sucesso"])
check("GET /produtos/busca preco_min inválido -> 400", c.get("/produtos/busca?preco_min=abc"), 400, ["erro","sucesso"])
check("PUT /produtos categoria inválida -> 400", c.put("/produtos/1", json={"nome":"Teste","preco":1,"estoque":1,"categoria":"xxx"}), 400, ["erro","sucesso"])

print("\n== usuários e login ==")
check("GET /usuarios", c.get("/usuarios"), 200, ["dados","sucesso"],
      lambda b: "senha vazada!" if any("senha" in u for u in b["dados"]) else None)
check("GET /usuarios/1", c.get("/usuarios/1"), 200, ["dados","sucesso"],
      lambda b: "senha vazada!" if "senha" in b["dados"] else None)
check("GET /usuarios/9999 (404)", c.get("/usuarios/9999"), 404, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Usuário não encontrado" else f"msg '{b['erro']}'")
u = check("POST /usuarios", c.post("/usuarios", json={"nome":"Novo","email":"novo@email.com","senha":"segredo123"}), 201, ["dados","sucesso"])
check("POST /usuarios faltando campo", c.post("/usuarios", json={"nome":"X"}), 400, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Nome, email e senha são obrigatórios" else f"msg '{b['erro']}'")
check("POST /login seed (senha hasheada)", c.post("/login", json={"email":"admin@loja.com","senha":"admin123"}), 200,
      ["dados","sucesso","mensagem"],
      lambda b: None if set(b["dados"])=={"id","nome","email","tipo"} and b["mensagem"]=="Login OK" else f"dados {sorted(b['dados'])}")
check("POST /login usuário novo", c.post("/login", json={"email":"novo@email.com","senha":"segredo123"}), 200, ["dados","sucesso","mensagem"])
check("POST /login senha errada (401)", c.post("/login", json={"email":"admin@loja.com","senha":"errada"}), 401, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Email ou senha inválidos" else f"msg '{b['erro']}'")
check("POST /login SQL injection bloqueado", c.post("/login", json={"email":"admin@loja.com' OR '1'='1","senha":"x' OR '1'='1"}), 401, ["erro","sucesso"])
check("POST /login sem campos", c.post("/login", json={"email":""}), 400, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Email e senha são obrigatórios" else f"msg '{b['erro']}'")

print("\n== pedidos ==")
estoque_antes = c.get("/produtos/2").get_json()["dados"]["estoque"]
p = check("POST /pedidos", c.post("/pedidos", json={"usuario_id":2,"itens":[{"produto_id":2,"quantidade":2},{"produto_id":3,"quantidade":1}]}),
          201, ["dados","sucesso","mensagem"],
          lambda b: None if set(b["dados"])=={"pedido_id","total"} and b["mensagem"]=="Pedido criado com sucesso" else "payload divergente")
esperado = round(89.90*2 + 299.90, 2)
check(f"  total calculado == {esperado}", c.get("/pedidos"), 200, None,
      lambda b: None if round(p["dados"]["total"],2)==esperado else f"total {p['dados']['total']} != {esperado}")
check("  estoque debitado", c.get("/produtos/2"), 200, None,
      lambda b: None if b["dados"]["estoque"]==estoque_antes-2 else f"estoque {b['dados']['estoque']} != {estoque_antes-2}")
check("GET /pedidos", c.get("/pedidos"), 200, ["dados","sucesso"],
      lambda b: None if len(b["dados"])==1 and len(b["dados"][0]["itens"])==2 else "estrutura divergente")
campos_pedido = {"id","usuario_id","status","total","criado_em","itens"}
campos_item = {"produto_id","produto_nome","quantidade","preco_unitario"}
check("  campos do pedido e do item", c.get("/pedidos"), 200, None,
      lambda b: None if set(b["dados"][0])==campos_pedido and set(b["dados"][0]["itens"][0])==campos_item
      else f"pedido {sorted(set(b['dados'][0]) ^ campos_pedido)} item {sorted(set(b['dados'][0]['itens'][0]) ^ campos_item)}")
check("GET /pedidos/usuario/2", c.get("/pedidos/usuario/2"), 200, ["dados","sucesso"],
      lambda b: None if len(b["dados"])==1 else f"{len(b['dados'])} pedidos")
check("GET /pedidos/usuario/999 (vazio)", c.get("/pedidos/usuario/999"), 200, ["dados","sucesso"],
      lambda b: None if b["dados"]==[] else "esperava lista vazia")
check("POST /pedidos produto inexistente (400)", c.post("/pedidos", json={"usuario_id":2,"itens":[{"produto_id":9999,"quantidade":1}]}), 400,
      ["erro","sucesso"], lambda b: None if b["erro"]=="Produto 9999 não encontrado" else f"msg '{b['erro']}'")
check("POST /pedidos estoque insuficiente (400)", c.post("/pedidos", json={"usuario_id":2,"itens":[{"produto_id":6,"quantidade":9999}]}), 400,
      ["erro","sucesso"], lambda b: None if b["erro"]=="Estoque insuficiente para Cadeira Gamer" else f"msg '{b['erro']}'")
check("POST /pedidos sem itens (400)", c.post("/pedidos", json={"usuario_id":2,"itens":[]}), 400, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Pedido deve ter pelo menos 1 item" else f"msg '{b['erro']}'")
check("POST /pedidos sem usuario_id (400)", c.post("/pedidos", json={"itens":[{"produto_id":1,"quantidade":1}]}), 400, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Usuario ID é obrigatório" else f"msg '{b['erro']}'")
check("POST /pedidos item malformado -> 400 (antes 500)", c.post("/pedidos", json={"usuario_id":2,"itens":[{"produto_id":1}]}), 400, ["erro","sucesso"])

print("\n== rollback transacional ==")
estoque_1 = c.get("/produtos/1").get_json()["dados"]["estoque"]
estoque_4 = c.get("/produtos/4").get_json()["dados"]["estoque"]
pedidos_antes = len(c.get("/pedidos").get_json()["dados"])
c.post("/pedidos", json={"usuario_id":2,"itens":[{"produto_id":1,"quantidade":1},{"produto_id":4,"quantidade":99999}]})
check("  nenhum estoque debitado após falha", c.get("/produtos/1"), 200, None,
      lambda b: None if b["dados"]["estoque"]==estoque_1 else f"estoque debitado! {b['dados']['estoque']} != {estoque_1}")
check("  nenhum pedido parcial gravado", c.get("/pedidos"), 200, None,
      lambda b: None if len(b["dados"])==pedidos_antes else f"{len(b['dados'])} pedidos != {pedidos_antes}")

print("\n== status de pedido ==")
pedido_id = p["dados"]["pedido_id"]
check("PUT /pedidos/<id>/status", c.put(f"/pedidos/{pedido_id}/status", json={"status":"aprovado"}), 200, ["sucesso","mensagem"],
      lambda b: None if b["mensagem"]=="Status atualizado" else "msg divergente")
check("  status persistido", c.get("/pedidos"), 200, None,
      lambda b: None if b["dados"][0]["status"]=="aprovado" else f"status {b['dados'][0]['status']}")
check("PUT status inválido (400)", c.put(f"/pedidos/{pedido_id}/status", json={"status":"xpto"}), 400, ["erro","sucesso"],
      lambda b: None if b["erro"]=="Status inválido" else f"msg '{b['erro']}'")
check("PUT status pedido inexistente -> 404 (antes 200)", c.put("/pedidos/9999/status", json={"status":"aprovado"}), 404, ["erro","sucesso"])

print("\n== relatório de vendas ==")
campos_rel = {"total_pedidos","faturamento_bruto","desconto_aplicavel","faturamento_liquido",
              "pedidos_pendentes","pedidos_aprovados","pedidos_cancelados","ticket_medio"}
check("GET /relatorios/vendas", c.get("/relatorios/vendas"), 200, ["dados","sucesso"],
      lambda b: None if set(b["dados"])==campos_rel else f"campos {sorted(set(b['dados']) ^ campos_rel)}")
check("  contagens coerentes", c.get("/relatorios/vendas"), 200, None,
      lambda b: None if b["dados"]["total_pedidos"]==1 and b["dados"]["pedidos_aprovados"]==1
      and b["dados"]["pedidos_pendentes"]==0 else f"contagens {b['dados']}")

from src.services import ReportService
print("\n== faixas de desconto (idênticas ao original) ==")
for faturamento, esperado in [(500,0), (1000,0), (1500,30.0), (5000,100.0), (7000,350.0), (10000,500.0), (20000,2000.0)]:
    total += 1
    obtido = ReportService.calcular_desconto(faturamento)
    ok = abs(obtido - esperado) < 1e-9
    print(f"  [{'ok ' if ok else 'FALHA'}] faturamento {faturamento} -> desconto {obtido} (esperado {esperado})")
    if not ok: falhas.append(f"desconto {faturamento}")

print("\n== rotas removidas ==")
for rota in ["/admin/query", "/admin/reset-db"]:
    check(f"POST {rota} -> 404", c.post(rota, json={"sql":"SELECT 1"}), 404, ["erro","sucesso"])

print("\n== SQL injection nos demais vetores ==")
c.post("/produtos", json={"nome":"x', 1); DROP TABLE produtos; --","preco":1,"estoque":1})
check("  tabela produtos intacta após payload de DROP", c.get("/produtos"), 200, ["dados","sucesso"])
check("  busca com quote não quebra", c.get("/produtos/busca?q=%27%20OR%20%271%27%3D%271"), 200, ["dados","total","sucesso"],
      lambda b: None if b["total"]==0 else f"injection retornou {b['total']} linhas")

print("\n" + "="*62)
print(f"{total - len(falhas)}/{total} verificações passaram")
if falhas:
    print("FALHAS:", falhas)
print("="*62)
raise SystemExit(1 if falhas else 0)
