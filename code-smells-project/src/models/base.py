class BaseModel:
    """Base dos models: recebe a conexão por injeção, nunca a cria."""

    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    @property
    def connection(self):
        return self._connection_provider()
