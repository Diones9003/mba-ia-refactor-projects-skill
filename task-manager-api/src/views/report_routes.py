"""Rotas de relatórios."""
from flask import Blueprint

from src.middlewares.auth import require_auth


def create_report_blueprint(controller):
    blueprint = Blueprint('reports', __name__)

    blueprint.add_url_rule(
        '/reports/summary', 'summary_report',
        require_auth(controller.summary), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/reports/user/<int:user_id>', 'user_report',
        require_auth(controller.user_report), methods=['GET'],
    )
    return blueprint
