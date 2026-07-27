from src.config.constants import (
    STATUS_PEDIDO_APROVADO,
    STATUS_PEDIDO_CANCELADO,
    STATUS_PEDIDO_PENDENTE,
)
from src.models.base import BaseModel

# Uma query agregada substitui as cinco COUNT/SUM separadas do código original.
SQL_RESUMO = """
    SELECT
        COUNT(*) AS total_pedidos,
        COALESCE(SUM(total), 0) AS faturamento,
        SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes,
        SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados,
        SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados
    FROM pedidos
"""


class ReportModel(BaseModel):
    """Consultas agregadas usadas pelo relatório de vendas."""

    def resumo_pedidos(self):
        row = self.connection.execute(
            SQL_RESUMO,
            (
                STATUS_PEDIDO_PENDENTE,
                STATUS_PEDIDO_APROVADO,
                STATUS_PEDIDO_CANCELADO,
            ),
        ).fetchone()

        return {
            "total_pedidos": row["total_pedidos"],
            "faturamento": row["faturamento"] or 0,
            "pendentes": row["pendentes"] or 0,
            "aprovados": row["aprovados"] or 0,
            "cancelados": row["cancelados"] or 0,
        }

    def verificar_conexao(self):
        self.connection.execute("SELECT 1").fetchone()
        return True
