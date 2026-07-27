"""Rotas de task.

O blueprint é criado por uma função que recebe o controller já montado — é assim
que a injeção de dependência chega até a camada HTTP, sem singletons de módulo.
"""
from flask import Blueprint

from src.middlewares.auth import require_auth


def create_task_blueprint(controller):
    blueprint = Blueprint('tasks', __name__)

    # Rotas literais antes das paramétricas para deixar a precedência explícita
    # (o conversor `<int:...>` já não casaria com "search"/"stats", mas a ordem
    # documenta a intenção).
    blueprint.add_url_rule(
        '/tasks/search', 'search_tasks',
        require_auth(controller.search_tasks), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/tasks/stats', 'task_stats',
        require_auth(controller.task_stats), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/tasks', 'list_tasks',
        require_auth(controller.list_tasks), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/tasks', 'create_task',
        require_auth(controller.create_task), methods=['POST'],
    )
    blueprint.add_url_rule(
        '/tasks/<int:task_id>', 'get_task',
        require_auth(controller.get_task), methods=['GET'],
    )
    blueprint.add_url_rule(
        '/tasks/<int:task_id>', 'update_task',
        require_auth(controller.update_task), methods=['PUT'],
    )
    blueprint.add_url_rule(
        '/tasks/<int:task_id>', 'delete_task',
        require_auth(controller.delete_task), methods=['DELETE'],
    )
    return blueprint
