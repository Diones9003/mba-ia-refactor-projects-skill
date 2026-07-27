from flask import request

from src.errors import NotFoundError
from src.middlewares.validation import (
    obter_json_obrigatorio,
    validar_payload_produto,
    validar_preco_opcional,
)


class ProductController:
    """Orquestra os endpoints de produto: entrada validada -> model -> saída."""

    def __init__(self, product_model):
        self._product_model = product_model

    def listar(self):
        return self._product_model.find_all()

    def buscar(self, produto_id):
        produto = self._product_model.find_by_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado")
        return produto

    def pesquisar(self):
        return self._product_model.search(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=validar_preco_opcional(request.args.get("preco_min"), "preco_min"),
            preco_max=validar_preco_opcional(request.args.get("preco_max"), "preco_max"),
        )

    def criar(self):
        payload = validar_payload_produto(obter_json_obrigatorio())
        return self._product_model.create(**payload)

    def atualizar(self, produto_id):
        if self._product_model.find_by_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")

        payload = validar_payload_produto(obter_json_obrigatorio())
        self._product_model.update(produto_id, **payload)

    def deletar(self, produto_id):
        if not self._product_model.delete(produto_id):
            raise NotFoundError("Produto não encontrado")
