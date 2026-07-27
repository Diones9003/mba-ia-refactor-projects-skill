from src.errors import ValidationError
from src.middlewares.validation import obter_json_obrigatorio, validar_itens_pedido


class OrderController:
    """Orquestra os endpoints de pedido. Regra de negócio fica no OrderService."""

    def __init__(self, order_service):
        self._order_service = order_service

    def listar(self):
        return self._order_service.listar()

    def listar_por_usuario(self, usuario_id):
        return self._order_service.listar_por_usuario(usuario_id)

    def criar(self):
        dados = obter_json_obrigatorio()

        usuario_id = dados.get("usuario_id")
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")

        itens = validar_itens_pedido(dados.get("itens", []))
        return self._order_service.criar(usuario_id, itens)

    def atualizar_status(self, pedido_id):
        dados = obter_json_obrigatorio()
        self._order_service.alterar_status(pedido_id, dados.get("status", ""))
