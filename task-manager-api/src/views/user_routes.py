"""Rotas de usuário."""
from flask import Blueprint

from src.config.constants import ROLE_ADMIN
from src.middlewares.auth import require_auth, require_role


def create_user_blueprint(controller):
    blueprint = Blueprint('users', __name__)

    blueprint.add_url_rule(
        '/users', 'list_users',
        require_auth(controller.list_users), methods=['GET'],
    )
    # Cadastro é público, mas escolher `role` exige privilégio de admin —
    # a checagem vive no UserService.
    blueprint.add_url_rule(
        '/users', 'create_user', controller.create_user, methods=['POST'],
    )
    blueprint.add_url_rule(
        '/users/<int:user_id>', 'get_user',
        require_auth(controller.get_user), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/users/<int:user_id>', 'update_user',
        require_auth(controller.update_user), methods=['PUT'],
    )
    blueprint.add_url_rule(
        '/users/<int:user_id>', 'delete_user',
        require_role(ROLE_ADMIN)(controller.delete_user), methods=['DELETE'],
    )
    blueprint.add_url_rule(
        '/users/<int:user_id>/tasks', 'list_user_tasks',
        require_auth(controller.list_user_tasks), methods=['GET'],
    )
    return blueprint
