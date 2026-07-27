from flask import Blueprint

from src.views.serializers import resposta_bruta, resposta_dados


def create_system_blueprint(system_controller):
    blueprint = Blueprint("sistema", __name__)

    @blueprint.get("/")
    def index():
        return resposta_bruta(system_controller.index())

    @blueprint.get("/relatorios/vendas")
    def relatorio_vendas():
        return resposta_dados(system_controller.relatorio_vendas())

    @blueprint.get("/health")
    def health_check():
        return resposta_bruta(system_controller.health())

    return blueprint
