from flask import Blueprint

from src.views.serializers import resposta_dados, resposta_mensagem


def create_order_blueprint(order_controller):
    blueprint = Blueprint("pedidos", __name__)

    @blueprint.post("/pedidos")
    def criar_pedido():
        resultado = order_controller.criar()
        return resposta_dados(
            resultado, status=201, mensagem="Pedido criado com sucesso"
        )

    @blueprint.get("/pedidos")
    def listar_todos_pedidos():
        return resposta_dados(order_controller.listar())

    @blueprint.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        return resposta_dados(order_controller.listar_por_usuario(usuario_id))

    @blueprint.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        order_controller.atualizar_status(pedido_id)
        return resposta_mensagem("Status atualizado")

    return blueprint
