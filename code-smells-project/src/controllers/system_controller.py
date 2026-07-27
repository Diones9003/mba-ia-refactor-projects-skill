class SystemController:
    """Endpoints de infraestrutura: índice, health check e relatório de vendas."""

    ENDPOINTS = {
        "produtos": "/produtos",
        "usuarios": "/usuarios",
        "pedidos": "/pedidos",
        "login": "/login",
        "relatorios": "/relatorios/vendas",
        "health": "/health",
    }

    def __init__(self, config, report_service, report_model, contadores):
        self._config = config
        self._report_service = report_service
        self._report_model = report_model
        self._contadores = contadores

    def index(self):
        return {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": self._config.API_VERSION,
            "endpoints": self.ENDPOINTS,
        }

    def relatorio_vendas(self):
        return self._report_service.vendas()

    def health(self):
        """Payload enxuto: sem secret key, sem db_path, sem flag de debug."""
        self._report_model.verificar_conexao()
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                nome: contar() for nome, contar in self._contadores.items()
            },
            "versao": self._config.API_VERSION,
            "ambiente": self._config.ENVIRONMENT,
        }
