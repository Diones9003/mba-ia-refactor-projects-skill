from flask import Blueprint

from src.views.serializers import resposta_dados


def create_user_blueprint(user_controller):
    blueprint = Blueprint("usuarios", __name__)

    @blueprint.get("/usuarios")
    def listar_usuarios():
        return resposta_dados(user_controller.listar())

    @blueprint.get("/usuarios/<int:usuario_id>")
    def buscar_usuario(usuario_id):
        return resposta_dados(user_controller.buscar(usuario_id))

    @blueprint.post("/usuarios")
    def criar_usuario():
        usuario_id = user_controller.criar()
        return resposta_dados({"id": usuario_id}, status=201)

    @blueprint.post("/login")
    def login():
        usuario = user_controller.login()
        return resposta_dados(usuario, mensagem="Login OK")

    return blueprint
