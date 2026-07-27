import sqlite3

from flask import g, has_app_context


def create_connection(db_path):
    """Cria uma conexão SQLite configurada (rows como dict, FKs ativas)."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


class ConnectionProvider:
    """Fornece a conexão do escopo atual.

    Substitui o singleton global do código original: dentro de um request a
    conexão vive em `flask.g` e é fechada no teardown, então uma transação
    pendente nunca "vaza" para outra requisição. Fora do contexto de app
    (scripts, testes) mantém uma conexão própria e reutilizável.

    É injetado nos models — quem testa pode passar qualquer callable que
    devolva uma conexão (ex.: apontando para `:memory:`).
    """

    CHAVE_CONTEXTO = "db_connection"

    def __init__(self, db_path):
        self.db_path = db_path
        self._conexao_fora_de_request = None

    def __call__(self):
        if has_app_context():
            if self.CHAVE_CONTEXTO not in g:
                setattr(g, self.CHAVE_CONTEXTO, create_connection(self.db_path))
            return getattr(g, self.CHAVE_CONTEXTO)

        if self._conexao_fora_de_request is None:
            self._conexao_fora_de_request = create_connection(self.db_path)
        return self._conexao_fora_de_request

    def close(self, exception=None):
        """Registrado como `teardown_appcontext` na factory da aplicação."""
        connection = g.pop(self.CHAVE_CONTEXTO, None)
        if connection is not None:
            connection.close()
