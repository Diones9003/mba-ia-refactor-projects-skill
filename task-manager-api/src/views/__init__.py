"""Camada View: blueprints (roteamento) + serializers (objeto → JSON)."""
from src.views.auth_routes import create_auth_blueprint
from src.views.category_routes import create_category_blueprint
from src.views.meta_routes import create_meta_blueprint
from src.views.report_routes import create_report_blueprint
from src.views.task_routes import create_task_blueprint
from src.views.user_routes import create_user_blueprint

__all__ = [
    'create_auth_blueprint',
    'create_category_blueprint',
    'create_meta_blueprint',
    'create_report_blueprint',
    'create_task_blueprint',
    'create_user_blueprint',
]
