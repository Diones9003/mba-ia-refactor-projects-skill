from src.config.constants import FAIXAS_DESCONTO


class ReportService:
    """Cálculo do relatório de vendas — regra de desconto isolada e testável."""

    def __init__(self, report_model):
        self._report_model = report_model

    def vendas(self):
        resumo = self._report_model.resumo_pedidos()
        faturamento = resumo["faturamento"]
        total_pedidos = resumo["total_pedidos"]
        desconto = self.calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": (
                round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
            ),
        }

    @staticmethod
    def calcular_desconto(faturamento):
        for faturamento_minimo, percentual in FAIXAS_DESCONTO:
            if faturamento > faturamento_minimo:
                return faturamento * percentual
        return 0
