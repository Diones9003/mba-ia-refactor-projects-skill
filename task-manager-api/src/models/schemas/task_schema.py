"""Validação de entrada de task.

`load_create` e `load_update` devolvem um dicionário com os campos já validados e
convertidos. A ordem das checagens reproduz exatamente o contrato original.
"""
from src.config.constants import (
    DATE_INPUT_FORMAT_HINT,
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
)
from src.exceptions import ValidationError
from src.models.schemas.base import (
    MISSING,
    field,
    parse_int_param,
    require_payload,
    validate_choice,
    validate_int_range,
    validate_optional_text,
    validate_string,
)
from src.utils.datetime_utils import parse_date

# Mensagens do contrato original, centralizadas.
MSG_TITLE_REQUIRED = 'Título é obrigatório'
MSG_TITLE_SHORT = 'Título muito curto'
MSG_TITLE_LONG = 'Título muito longo'
MSG_TITLE_TYPE = 'Título inválido'
MSG_STATUS_INVALID = 'Status inválido'
MSG_PRIORITY_INVALID = f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}'
MSG_DESCRIPTION_INVALID = 'Descrição inválida'
MSG_TAGS_INVALID = 'Tags inválidas'
MSG_REFERENCE_INVALID = 'Referência inválida'
# O texto do erro de data difere entre criar e atualizar no código original.
MSG_DATE_INVALID_CREATE = f'Formato de data inválido. Use {DATE_INPUT_FORMAT_HINT}'
MSG_DATE_INVALID_UPDATE = 'Formato de data inválido'


def _validate_reference(value, message=MSG_REFERENCE_INVALID):
    """Valida uma FK opcional (`user_id`/`category_id`): inteiro positivo ou nulo."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(message)
    return value


def _validate_due_date(value, message):
    if value is None:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError(message)
    return parsed


def _validate_tags(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if any(not isinstance(tag, (str, int, float)) for tag in value):
            raise ValidationError(MSG_TAGS_INVALID)
        return list(value)
    if isinstance(value, str):
        return value
    raise ValidationError(MSG_TAGS_INVALID)


def load_create(data):
    """Valida o payload de `POST /tasks`."""
    require_payload(data)

    title = field(data, 'title')
    if title is MISSING or title is None or title == '':
        raise ValidationError(MSG_TITLE_REQUIRED)
    result = {
        'title': validate_string(
            title,
            empty_message=MSG_TITLE_REQUIRED,
            type_message=MSG_TITLE_TYPE,
            min_length=MIN_TITLE_LENGTH,
            short_message=MSG_TITLE_SHORT,
            max_length=MAX_TITLE_LENGTH,
            long_message=MSG_TITLE_LONG,
        )
    }

    description = data.get('description', '')
    result['description'] = validate_optional_text(description, MSG_DESCRIPTION_INVALID)

    status = data.get('status', DEFAULT_STATUS)
    result['status'] = validate_choice(status, VALID_STATUSES, MSG_STATUS_INVALID)

    priority = data.get('priority', DEFAULT_PRIORITY)
    result['priority'] = validate_int_range(
        priority, MIN_PRIORITY, MAX_PRIORITY, MSG_PRIORITY_INVALID
    )

    result['user_id'] = _validate_reference(data.get('user_id'))
    result['category_id'] = _validate_reference(data.get('category_id'))
    result['due_date'] = _validate_due_date(
        data.get('due_date'), MSG_DATE_INVALID_CREATE
    )
    result['tags'] = _validate_tags(data.get('tags'))
    return result


def load_update(data):
    """Valida o payload de `PUT /tasks/<id>` — só os campos presentes."""
    require_payload(data)
    result = {}

    if 'title' in data:
        result['title'] = validate_string(
            data['title'],
            # No update o contrato original não tem mensagem de "obrigatório":
            # título vazio cai na regra de tamanho mínimo.
            empty_message=MSG_TITLE_SHORT,
            type_message=MSG_TITLE_TYPE,
            min_length=MIN_TITLE_LENGTH,
            short_message=MSG_TITLE_SHORT,
            max_length=MAX_TITLE_LENGTH,
            long_message=MSG_TITLE_LONG,
        )

    if 'description' in data:
        result['description'] = validate_optional_text(
            data['description'], MSG_DESCRIPTION_INVALID
        )

    if 'status' in data:
        result['status'] = validate_choice(
            data['status'], VALID_STATUSES, MSG_STATUS_INVALID
        )

    if 'priority' in data:
        result['priority'] = validate_int_range(
            data['priority'], MIN_PRIORITY, MAX_PRIORITY, MSG_PRIORITY_INVALID
        )

    if 'user_id' in data:
        result['user_id'] = _validate_reference(data['user_id'])

    if 'category_id' in data:
        result['category_id'] = _validate_reference(data['category_id'])

    if 'due_date' in data:
        result['due_date'] = _validate_due_date(
            data['due_date'], MSG_DATE_INVALID_UPDATE
        )

    if 'tags' in data:
        result['tags'] = _validate_tags(data['tags'])

    return result


def load_search(args):
    """Valida os filtros de `GET /tasks/search`."""
    return {
        'term': (args.get('q') or '').strip() or None,
        'status': (args.get('status') or '').strip() or None,
        'priority': parse_int_param(
            args.get('priority'), 'Parâmetro priority inválido'
        ),
        'user_id': parse_int_param(args.get('user_id'), 'Parâmetro user_id inválido'),
    }
