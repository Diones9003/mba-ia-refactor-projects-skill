import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_USUARIO_CLIENTE
from src.errors import BusinessRuleError
from src.models.base import BaseModel

# `senha` fica deliberadamente fora da projeção: o hash nunca sai da camada de dados.
COLUNAS = "id, nome, email, tipo, criado_em"


class UserModel(BaseModel):
    """Acesso a dados de usuários, com hash de senha encapsulado."""

    def find_all(self):
        rows = self.connection.execute(f"SELECT {COLUNAS} FROM usuarios").fetchall()
        return [dict(row) for row in rows]

    def find_by_id(self, usuario_id):
        row = self.connection.execute(
            f"SELECT {COLUNAS} FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return dict(row) if row else None

    def create(self, nome, email, senha, tipo=TIPO_USUARIO_CLIENTE):
        connection = self.connection
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                    (nome, email, generate_password_hash(senha), tipo),
                )
        except sqlite3.IntegrityError as exc:
            raise BusinessRuleError("E-mail já cadastrado") from exc
        return cursor.lastrowid

    def authenticate(self, email, senha):
        """Busca pelo e-mail e compara o hash — a senha nunca entra na query."""
        row = self.connection.execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None or not check_password_hash(row["senha"], senha):
            return None

        usuario = dict(row)
        usuario.pop("senha")
        usuario.pop("criado_em", None)
        return usuario

    def count(self):
        return self.connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
