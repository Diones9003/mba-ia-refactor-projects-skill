import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import AppError

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno"


def register_error_handlers(app):
    """Ponto único de tratamento de erros.

    Substitui os `try/except Exception` repetidos em todos os 15 handlers do
    código original, que ainda devolviam `str(e)` ao cliente — vazando detalhes
    internos (inclusive SQL) na resposta.
    """

    @app.errorhandler(AppError)
    def tratar_erro_de_dominio(erro):
        logger.info("Erro de domínio (%s): %s", erro.status_code, erro.mensagem)
        return jsonify({"erro": erro.mensagem, "sucesso": False}), erro.status_code

    @app.errorhandler(HTTPException)
    def tratar_erro_http(erro):
        return (
            jsonify({"erro": erro.description, "sucesso": False}),
            erro.code,
        )

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        # O detalhe vai para o log; o cliente recebe mensagem genérica.
        logger.exception("Erro inesperado: %s", erro)
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO, "sucesso": False}), 500
