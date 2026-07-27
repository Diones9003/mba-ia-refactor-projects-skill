"""Validação de entrada de usuário."""
import re

from src.config.constants import (
    DEFAULT_ROLE,
    EMAIL_PATTERN,
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    VALID_ROLES,
)
from src.exceptions import ValidationError
from src.models.schemas.base import (
    MISSING,
    field,
    require_payload,
    validate_bool,
    validate_choice,
    validate_string,
)

_EMAIL_RE = re.compile(EMAIL_PATTERN)

MSG_NAME_REQUIRED = 'Nome é obrigatório'
MSG_NAME_TYPE = 'Nome inválido'
MSG_EMAIL_REQUIRED = 'Email é obrigatório'
MSG_EMAIL_INVALID = 'Email inválido'
MSG_PASSWORD_REQUIRED = 'Senha é obrigatória'
MSG_ROLE_INVALID = 'Role inválido'
MSG_ACTIVE_INVALID = 'Campo active deve ser booleano'
MSG_EMAIL_TAKEN = 'Email já cadastrado'


def password_too_short_message(min_length):
    """Mensagem de senha curta usada na **criação**."""
    return f'Senha deve ter no mínimo {min_length} caracteres'


#: Mensagem de senha curta usada na **atualização** (texto diferente no original).
MSG_PASSWORD_SHORT_UPDATE = 'Senha muito curta'


def is_valid_email(email):
    return isinstance(email, str) and bool(_EMAIL_RE.match(email))


def _validate_email(value):
    if value is None or value == '':
        raise ValidationError(MSG_EMAIL_REQUIRED)
    if not is_valid_email(value):
        raise ValidationError(MSG_EMAIL_INVALID)
    if len(value) > MAX_EMAIL_LENGTH:
        raise ValidationError(MSG_EMAIL_INVALID)
    return value


def _validate_password(value, min_length, short_message):
    if value is None or value == '':
        raise ValidationError(MSG_PASSWORD_REQUIRED)
    if not isinstance(value, str):
        raise ValidationError(short_message)
    if len(value) < min_length:
        raise ValidationError(short_message)
    return value


def load_create(data, min_password_length):
    """Valida o payload de `POST /users`, na ordem do contrato original."""
    require_payload(data)

    name = field(data, 'name')
    if name is MISSING or name is None or name == '':
        raise ValidationError(MSG_NAME_REQUIRED)

    email = field(data, 'email')
    if email is MISSING or email is None or email == '':
        raise ValidationError(MSG_EMAIL_REQUIRED)

    password = field(data, 'password')
    if password is MISSING or password is None or password == '':
        raise ValidationError(MSG_PASSWORD_REQUIRED)

    result = {
        'name': validate_string(
            name,
            empty_message=MSG_NAME_REQUIRED,
            type_message=MSG_NAME_TYPE,
            max_length=MAX_NAME_LENGTH,
            long_message=MSG_NAME_TYPE,
        ),
        'email': _validate_email(email),
        'password': _validate_password(
            password,
            min_password_length,
            password_too_short_message(min_password_length),
        ),
        'role': validate_choice(
            data.get('role', DEFAULT_ROLE), VALID_ROLES, MSG_ROLE_INVALID
        ),
    }
    #: Sinaliza se o cliente pediu um role explicitamente — a autorização de
    #: quem pode escolher role é decidida no service, não aqui.
    result['role_requested'] = 'role' in data
    return result


def load_update(data, min_password_length):
    """Valida o payload de `PUT /users/<id>` — só os campos presentes."""
    require_payload(data)
    result = {}

    if 'name' in data:
        result['name'] = validate_string(
            data['name'],
            empty_message=MSG_NAME_REQUIRED,
            type_message=MSG_NAME_TYPE,
            max_length=MAX_NAME_LENGTH,
            long_message=MSG_NAME_TYPE,
        )

    if 'email' in data:
        result['email'] = _validate_email(data['email'])

    if 'password' in data:
        result['password'] = _validate_password(
            data['password'], min_password_length, MSG_PASSWORD_SHORT_UPDATE
        )

    if 'role' in data:
        result['role'] = validate_choice(data['role'], VALID_ROLES, MSG_ROLE_INVALID)

    if 'active' in data:
        result['active'] = validate_bool(data['active'], MSG_ACTIVE_INVALID)

    return result


def load_login(data):
    """Valida o payload de `POST /login`."""
    require_payload(data)
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    return {'email': email, 'password': password}
