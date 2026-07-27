import logging

from src.config.constants import STATUS_PEDIDO_APROVADO, STATUS_PEDIDO_CANCELADO

logger = logging.getLogger(__name__)


class NotificationService:
    """Ponto único de notificações.

    No código original os "envios" eram `print` dentro dos controllers, o que
    tornava o efeito dependente do caminho HTTP. Aqui ficam isolados e
    injetáveis — trocar por um provedor real (e-mail/SMS) não toca controller.
    """

    CANAIS_PEDIDO_CRIADO = ("email", "sms", "push")

    def pedido_criado(self, usuario_id, pedido_id):
        for canal in self.CANAIS_PEDIDO_CRIADO:
            logger.info(
                "Notificação pendente [%s]: pedido %s criado para usuário %s",
                canal,
                pedido_id,
                usuario_id,
            )

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == STATUS_PEDIDO_APROVADO:
            logger.info("Pedido %s aprovado — preparar envio", pedido_id)
        elif novo_status == STATUS_PEDIDO_CANCELADO:
            # O código original imprimia "Devolver estoque" sem nunca devolver.
            # A mensagem enganosa foi removida; a devolução de estoque continua
            # não implementada e segue registrada como pendência no relatório.
            logger.info("Pedido %s cancelado", pedido_id)
