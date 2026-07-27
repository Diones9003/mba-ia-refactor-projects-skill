"""Error handling centralizado.

Um único ponto traduz exceções em respostas JSON, substituindo os 12 `except:` nus
que existiam nos handlers — e garantindo que erros inesperados sejam **logados**
em vez de engolidos, e que a resposta nunca seja uma página HTML de traceback.
"""
import logging

from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from src.exceptions import AppError

logger = logging.getLogger(__name__)

MSG_INTERNAL = 'Erro interno'


def register_error_handlers(app, db):
    """Registra os handlers de erro na aplicação."""

    @app.errorhandler(AppError)
    def handle_app_error(error):
        # Erro de domínio previsto: nível informativo, sem stack trace.
        logger.info('%s: %s', type(error).__name__, error.message)
        return error.to_payload(), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # Mantém o status escolhido pelo Flask (404 de rota, 405, 415…) mas
        # responde em JSON, como o resto da API.
        return {'error': error.description}, error.code

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        db.session.rollback()
        logger.exception('Erro de banco de dados')
        return {'error': MSG_INTERNAL}, 500

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        db.session.rollback()
        logger.exception('Erro não tratado')
        return {'error': MSG_INTERNAL}, 500
