"""Autenticação: emissão e verificação de JWT.

Substitui o `'fake-jwt-token-' + str(user.id)` do código original — uma string
previsável, não assinada e sem expiração, que nenhuma rota verificava.
"""
from datetime import timedelta

import jwt

from src.exceptions import ForbiddenError, UnauthorizedError
from src.utils.datetime_utils import utcnow

MSG_INVALID_CREDENTIALS = 'Credenciais inválidas'
MSG_INACTIVE_USER = 'Usuário inativo'
MSG_TOKEN_MISSING = 'Token de autenticação ausente'
MSG_TOKEN_INVALID = 'Token inválido'
MSG_TOKEN_EXPIRED = 'Token expirado'


class AuthService:
    def __init__(self, session, user_model, secret_key, algorithm='HS256',
                 expiration_minutes=60):
        self.session = session
        self.user_model = user_model
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def authenticate(self, email, password):
        """Valida credenciais e devolve `(user, token)`.

        A ordem das checagens reproduz o contrato original: usuário inexistente e
        senha errada respondem igual (401), e a conta inativa responde 403 —
        depois de a senha ter sido conferida.
        """
        user = self.user_model.get_by_email(email)
        if user is None:
            raise UnauthorizedError(MSG_INVALID_CREDENTIALS)

        if not user.check_password(password):
            raise UnauthorizedError(MSG_INVALID_CREDENTIALS)

        # `check_password` reescreve credenciais MD5 legadas como hash forte;
        # o commit persiste essa migração transparente.
        self.session.commit()

        if not user.active:
            raise ForbiddenError(MSG_INACTIVE_USER)

        return user, self.issue_token(user)

    def issue_token(self, user):
        issued_at = utcnow()
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'role': user.role,
            'iat': issued_at,
            'exp': issued_at + timedelta(minutes=self.expiration_minutes),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token):
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise UnauthorizedError(MSG_TOKEN_EXPIRED) from None
        except jwt.InvalidTokenError:
            raise UnauthorizedError(MSG_TOKEN_INVALID) from None

    def user_from_token(self, token):
        """Resolve o usuário de um token, recusando contas removidas ou inativas."""
        claims = self.decode_token(token)
        try:
            user_id = int(claims.get('sub'))
        except (TypeError, ValueError):
            raise UnauthorizedError(MSG_TOKEN_INVALID) from None

        user = self.user_model.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError(MSG_TOKEN_INVALID)
        if not user.active:
            raise ForbiddenError(MSG_INACTIVE_USER)
        return user

    @staticmethod
    def extract_bearer_token(authorization_header):
        """Extrai o token de um header `Authorization: Bearer <token>`."""
        if not authorization_header:
            return None
        parts = authorization_header.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        return parts[1].strip() or None
