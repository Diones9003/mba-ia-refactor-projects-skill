from flask import Blueprint

from src.views.serializers import resposta_dados, resposta_mensagem


def create_product_blueprint(product_controller):
    blueprint = Blueprint("produtos", __name__)

    @blueprint.get("/produtos")
    def listar_produtos():
        return resposta_dados(product_controller.listar())

    @blueprint.get("/produtos/busca")
    def buscar_produtos():
        resultados = product_controller.pesquisar()
        return resposta_dados(resultados, total=len(resultados))

    @blueprint.get("/produtos/<int:produto_id>")
    def buscar_produto(produto_id):
        return resposta_dados(product_controller.buscar(produto_id))

    @blueprint.post("/produtos")
    def criar_produto():
        produto_id = product_controller.criar()
        return resposta_dados(
            {"id": produto_id}, status=201, mensagem="Produto criado"
        )

    @blueprint.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        product_controller.atualizar(produto_id)
        return resposta_mensagem("Produto atualizado")

    @blueprint.delete("/produtos/<int:produto_id>")
    def deletar_produto(produto_id):
        product_controller.deletar(produto_id)
        return resposta_mensagem("Produto deletado")

    return blueprint
