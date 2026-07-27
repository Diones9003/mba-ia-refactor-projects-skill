"""Rotas de metadados e healthcheck — públicas por definição."""
from flask import Blueprint


def create_meta_blueprint(controller):
    blueprint = Blueprint('meta', __name__)
    blueprint.add_url_rule('/', 'index', controller.index, methods=['GET'])
    blueprint.add_url_rule('/health', 'health', controller.health, methods=['GET'])
    return blueprint
