"""Autenticação e autorização transversais.

O código original não tinha nada disso: os 22 endpoints eram anônimos e o "token"
devolvido pelo login não era verificado em lugar algum.
"""
from functools import wraps

from flask import current_app, g, request

from src.exceptions import ForbiddenError, UnauthorizedError
from src.services.auth_service import MSG_TOKEN_MISSING

#: Chave usada para guardar o service de autenticação na aplicação.
AUTH_SERVICE_KEY = 'auth_service'


def register_auth(app, auth_service):
    """Disponibiliza o `AuthService` para os decorators via extensões do app."""
    app.extensions[AUTH_SERVICE_KEY] = auth_service


def _auth_service():
    return current_app.extensions[AUTH_SERVICE_KEY]


def _auth_required():
    return current_app.config.get('REQUIRE_AUTH', True)


def current_user():
    """Usuário autenticado da request atual, ou `None`."""
    return getattr(g, 'current_user', None)


def load_current_user():
    """Resolve o usuário do header `Authorization`, se houver.

    Roda como `before_request`: popula `g.current_user` de forma otimista para que
    rotas públicas também possam saber quem é o chamador (ex.: um admin criando
    usuário com role). Token ausente não é erro aqui — quem exige é o decorator.
    """
    g.current_user = None
    g.auth_error = None
    token = _auth_service().extract_bearer_token(request.headers.get('Authorization'))
    if not token:
        return
    try:
        g.current_user = _auth_service().user_from_token(token)
    except (UnauthorizedError, ForbiddenError) as error:
        # Um token ruim em rota pública não derruba a request, mas o motivo é
        # guardado para que a rota protegida responda com a causa correta em vez
        # de um genérico "token ausente".
        g.auth_error = error


def _reject_unauthenticated():
    """Levanta a exceção que descreve *por que* não há usuário autenticado."""
    raise getattr(g, 'auth_error', None) or UnauthorizedError(MSG_TOKEN_MISSING)


def require_auth(view):
    """Exige um token válido para acessar a rota."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _auth_required():
            return view(*args, **kwargs)
        if current_user() is None:
            _reject_unauthenticated()
        return view(*args, **kwargs)

    return wrapper


def require_role(*roles):
    """Exige um token válido cujo usuário tenha um dos papéis informados."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not _auth_required():
                return view(*args, **kwargs)
            user = current_user()
            if user is None:
                _reject_unauthenticated()
            if user.role not in roles:
                raise ForbiddenError(
                    'Permissão insuficiente para esta operação'
                )
            return view(*args, **kwargs)

        return wrapper

    return decorator
