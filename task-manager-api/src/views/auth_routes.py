"""Rotas de autenticação."""
from flask import Blueprint


def create_auth_blueprint(controller):
    blueprint = Blueprint('auth', __name__)
    blueprint.add_url_rule('/login', 'login', controller.login, methods=['POST'])
    return blueprint
