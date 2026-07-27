from src.config.constants import STATUS_PEDIDO_VALIDOS
from src.errors import NotFoundError, ValidationError


class OrderService:
    """Regras de negócio de pedidos: criação transacional e transição de status."""

    def __init__(self, order_model, notification_service):
        self._order_model = order_model
        self._notification_service = notification_service

    def listar(self):
        return self._order_model.find_all()

    def listar_por_usuario(self, usuario_id):
        return self._order_model.find_by_user(usuario_id)

    def criar(self, usuario_id, itens):
        resultado = self._order_model.create(usuario_id, itens)
        self._notification_service.pedido_criado(usuario_id, resultado["pedido_id"])
        return resultado

    def alterar_status(self, pedido_id, novo_status):
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise ValidationError("Status inválido")

        if not self._order_model.update_status(pedido_id, novo_status):
            raise NotFoundError("Pedido não encontrado")

        self._notification_service.status_alterado(pedido_id, novo_status)
