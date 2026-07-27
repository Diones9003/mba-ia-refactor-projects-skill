import logging

from flask import request

logger = logging.getLogger(__name__)


def register_request_logger(app):
    """Log estruturado de requests, sem PII no corpo.

    Substitui os `print` espalhados pelos controllers — inclusive os que
    registravam e-mails de tentativas de login em stdout.
    """

    @app.after_request
    def registrar(resposta):
        logger.info(
            "%s %s -> %s", request.method, request.path, resposta.status_code
        )
        return resposta
