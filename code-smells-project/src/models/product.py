from src.models.base import BaseModel

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


class ProductModel(BaseModel):
    """Acesso a dados de produtos. Todas as queries são parametrizadas."""

    def find_all(self):
        rows = self.connection.execute(f"SELECT {COLUNAS} FROM produtos").fetchall()
        return [dict(row) for row in rows]

    def find_by_id(self, produto_id):
        row = self.connection.execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return dict(row) if row else None

    def find_many_by_ids(self, produto_ids):
        """Busca em lote — evita uma query por item ao montar um pedido."""
        ids_unicos = list({produto_id for produto_id in produto_ids})
        if not ids_unicos:
            return {}

        placeholders = ", ".join("?" for _ in ids_unicos)
        rows = self.connection.execute(
            f"SELECT {COLUNAS} FROM produtos WHERE id IN ({placeholders})",
            tuple(ids_unicos),
        ).fetchall()
        return {row["id"]: dict(row) for row in rows}

    def search(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Busca com filtros opcionais, montada com placeholders (nunca concatenação)."""
        sql = f"SELECT {COLUNAS} FROM produtos WHERE 1 = 1"
        parametros = []

        if termo:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            padrao = f"%{termo}%"
            parametros.extend([padrao, padrao])
        if categoria:
            sql += " AND categoria = ?"
            parametros.append(categoria)
        if preco_min is not None:
            sql += " AND preco >= ?"
            parametros.append(preco_min)
        if preco_max is not None:
            sql += " AND preco <= ?"
            parametros.append(preco_max)

        rows = self.connection.execute(sql, tuple(parametros)).fetchall()
        return [dict(row) for row in rows]

    def create(self, nome, descricao, preco, estoque, categoria):
        connection = self.connection
        with connection:
            cursor = connection.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
                "VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def update(self, produto_id, nome, descricao, preco, estoque, categoria):
        connection = self.connection
        with connection:
            cursor = connection.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, "
                "estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )
        return cursor.rowcount > 0

    def delete(self, produto_id):
        connection = self.connection
        with connection:
            cursor = connection.execute(
                "DELETE FROM produtos WHERE id = ?", (produto_id,)
            )
        return cursor.rowcount > 0

    def count(self):
        return self.connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
