from src.errors import NotFoundError, UnauthorizedError
from src.middlewares.validation import (
    obter_json_obrigatorio,
    validar_credenciais,
    validar_payload_usuario,
)


class UserController:
    """Orquestra os endpoints de usuário e autenticação."""

    def __init__(self, user_model):
        self._user_model = user_model

    def listar(self):
        return self._user_model.find_all()

    def buscar(self, usuario_id):
        usuario = self._user_model.find_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self):
        payload = validar_payload_usuario(obter_json_obrigatorio())
        return self._user_model.create(**payload)

    def login(self):
        credenciais = validar_credenciais(obter_json_obrigatorio())
        usuario = self._user_model.authenticate(**credenciais)
        if usuario is None:
            raise UnauthorizedError("Email ou senha inválidos")
        return usuario
