"""Rotas de categoria.

No código original este CRUD estava registrado no blueprint de **relatórios**
(`routes/report_routes.py`). Os paths e métodos são os mesmos; só a organização mudou.
"""
from flask import Blueprint

from src.config.constants import ROLE_ADMIN, ROLE_MANAGER
from src.middlewares.auth import require_auth, require_role


def create_category_blueprint(controller):
    blueprint = Blueprint('categories', __name__)

    blueprint.add_url_rule(
        '/categories', 'list_categories',
        require_auth(controller.list_categories), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/categories', 'create_category',
        require_role(ROLE_ADMIN, ROLE_MANAGER)(controller.create_category),
        methods=['POST'],
    )
    blueprint.add_url_rule(
        '/categories/<int:category_id>', 'update_category',
        require_role(ROLE_ADMIN, ROLE_MANAGER)(controller.update_category),
        methods=['PUT'],
    )
    blueprint.add_url_rule(
        '/categories/<int:category_id>', 'delete_category',
        require_role(ROLE_ADMIN)(controller.delete_category), methods=['DELETE'],
    )
    return blueprint
