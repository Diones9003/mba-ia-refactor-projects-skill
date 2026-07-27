"""Regras de negócio de usuário."""
from src.config.constants import DEFAULT_ROLE
from src.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.models.schemas.user_schema import MSG_EMAIL_TAKEN

MSG_USER_NOT_FOUND = 'Usuário não encontrado'
MSG_ROLE_NOT_ALLOWED = 'Apenas administradores podem definir o role de um usuário'


class UserService:
    def __init__(self, session, user_model, task_model, enforce_authorization=True):
        self.session = session
        self.user_model = user_model
        self.task_model = task_model
        # Espelha `Config.REQUIRE_AUTH`: com a autenticação desligada não existe
        # requester para autorizar, então as checagens de privilégio ficam inertes
        # e o comportamento é o do contrato legado.
        self.enforce_authorization = enforce_authorization

    # --- Leitura ---

    def list_users(self, limit=None, offset=None):
        """Usuários + contagem de tasks em uma query (antes era um N+1 por `len(u.tasks)`)."""
        return self.user_model.list_with_task_counts(limit=limit, offset=offset)

    def get_user(self, user_id):
        user = self.user_model.get_by_id(user_id)
        if user is None:
            raise NotFoundError(MSG_USER_NOT_FOUND)
        return user

    def get_user_with_tasks(self, user_id):
        user = self.get_user(user_id)
        return user, self.task_model.list_by_user(user_id)

    # --- Escrita ---

    def create_user(self, payload, requester=None):
        """Cria usuário.

        Escolher o `role` é privilégio de administrador: no código original o
        campo vinha direto do corpo da requisição, permitindo que qualquer
        cliente anônimo se cadastrasse como `admin`.
        """
        role = payload.get('role', DEFAULT_ROLE)
        if payload.get('role_requested') and role != DEFAULT_ROLE:
            self._require_admin(requester)

        if self.user_model.get_by_email(payload['email']) is not None:
            raise ConflictError(MSG_EMAIL_TAKEN)

        user = self.user_model()
        user.name = payload['name']
        user.email = payload['email']
        user.set_password(payload['password'])
        user.role = role

        self.session.add(user)
        self.session.commit()
        return user

    def update_user(self, user_id, payload, requester=None):
        user = self.get_user(user_id)

        if 'role' in payload and payload['role'] != user.role:
            self._require_admin(requester)

        if 'email' in payload and self.user_model.email_taken_by_other(
            payload['email'], user_id
        ):
            raise ConflictError(MSG_EMAIL_TAKEN)

        if 'name' in payload:
            user.name = payload['name']
        if 'email' in payload:
            user.email = payload['email']
        if 'password' in payload:
            user.set_password(payload['password'])
        if 'role' in payload:
            user.role = payload['role']
        if 'active' in payload:
            user.active = payload['active']

        self.session.commit()
        return user

    def delete_user(self, user_id):
        """Remove o usuário; as tasks caem por cascade declarado no relacionamento."""
        user = self.get_user(user_id)
        self.session.delete(user)
        self.session.commit()

    # --- Autorização ---

    def _require_admin(self, requester):
        if not self.enforce_authorization:
            return
        if requester is None or not requester.is_admin():
            raise ForbiddenError(MSG_ROLE_NOT_ALLOWED)
