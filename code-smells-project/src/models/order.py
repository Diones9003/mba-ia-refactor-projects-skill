from src.config.constants import STATUS_PEDIDO_PENDENTE
from src.errors import BusinessRuleError
from src.models.base import BaseModel

COLUNAS = "id, usuario_id, status, total, criado_em"

# Um único JOIN traz os itens de todos os pedidos com o nome do produto,
# substituindo o N+1 (uma query por pedido + uma por item) do código original.
SQL_ITENS = """
    SELECT
        itens_pedido.pedido_id,
        itens_pedido.produto_id,
        itens_pedido.quantidade,
        itens_pedido.preco_unitario,
        produtos.nome AS produto_nome
    FROM itens_pedido
    LEFT JOIN produtos ON produtos.id = itens_pedido.produto_id
    WHERE itens_pedido.pedido_id IN ({placeholders})
    ORDER BY itens_pedido.id
"""

NOME_PRODUTO_DESCONHECIDO = "Desconhecido"


class OrderModel(BaseModel):
    """Acesso a dados de pedidos e seus itens."""

    def __init__(self, connection_provider, product_model):
        super().__init__(connection_provider)
        self._product_model = product_model

    def find_all(self):
        rows = self.connection.execute(
            f"SELECT {COLUNAS} FROM pedidos ORDER BY id"
        ).fetchall()
        return self._montar_pedidos(rows)

    def find_by_user(self, usuario_id):
        rows = self.connection.execute(
            f"SELECT {COLUNAS} FROM pedidos WHERE usuario_id = ? ORDER BY id",
            (usuario_id,),
        ).fetchall()
        return self._montar_pedidos(rows)

    def find_by_id(self, pedido_id):
        row = self.connection.execute(
            f"SELECT {COLUNAS} FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        if row is None:
            return None
        return self._montar_pedidos([row])[0]

    def create(self, usuario_id, itens):
        """Cria pedido, itens e baixa de estoque em uma única transação.

        Qualquer exceção no meio do caminho dispara rollback — o código original
        não tinha esse controle e podia deixar estoque debitado sem pedido.
        """
        connection = self.connection
        with connection:
            produtos = self._product_model.find_many_by_ids(
                [item["produto_id"] for item in itens]
            )
            total = self._calcular_total(itens, produtos)

            cursor = connection.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PEDIDO_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid

            connection.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                [
                    (
                        pedido_id,
                        item["produto_id"],
                        item["quantidade"],
                        produtos[item["produto_id"]]["preco"],
                    )
                    for item in itens
                ],
            )
            connection.executemany(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                [(item["quantidade"], item["produto_id"]) for item in itens],
            )

        return {"pedido_id": pedido_id, "total": total}

    def update_status(self, pedido_id, novo_status):
        connection = self.connection
        with connection:
            cursor = connection.execute(
                "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
            )
        return cursor.rowcount > 0

    def count(self):
        return self.connection.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    def _calcular_total(self, itens, produtos):
        """Valida disponibilidade e soma o total. Roda dentro da transação de `create`."""
        total = 0
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise BusinessRuleError(
                    f"Produto {item['produto_id']} não encontrado"
                )
            if produto["estoque"] < item["quantidade"]:
                raise BusinessRuleError(
                    f"Estoque insuficiente para {produto['nome']}"
                )
            total += produto["preco"] * item["quantidade"]
        return total

    def _montar_pedidos(self, rows):
        pedidos = [dict(row, itens=[]) for row in rows]
        if not pedidos:
            return []

        indice = {pedido["id"]: pedido for pedido in pedidos}
        placeholders = ", ".join("?" for _ in indice)
        itens = self.connection.execute(
            SQL_ITENS.format(placeholders=placeholders), tuple(indice)
        ).fetchall()

        for item in itens:
            indice[item["pedido_id"]]["itens"].append(
                {
                    "produto_id": item["produto_id"],
                    "produto_nome": item["produto_nome"] or NOME_PRODUTO_DESCONHECIDO,
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                }
            )
        return pedidos
