"""Validação de entrada de categoria."""
from src.config.constants import (
    DEFAULT_COLOR,
    MAX_CATEGORY_DESCRIPTION_LENGTH,
    MAX_CATEGORY_NAME_LENGTH,
)
from src.exceptions import ValidationError
from src.models.category import Category
from src.models.schemas.base import (
    MISSING,
    field,
    require_payload,
    validate_optional_text,
    validate_string,
)

MSG_NAME_REQUIRED = 'Nome é obrigatório'
MSG_NAME_TYPE = 'Nome inválido'
MSG_DESCRIPTION_INVALID = 'Descrição inválida'
MSG_COLOR_INVALID = 'Cor inválida. Use o formato #RRGGBB'


def _validate_color(value):
    """Valida a cor com o `is_valid_color` do model (antes era código morto no helper)."""
    if value is None:
        return DEFAULT_COLOR
    if not Category.is_valid_color(value):
        raise ValidationError(MSG_COLOR_INVALID)
    return value


def load_create(data):
    """Valida o payload de `POST /categories`."""
    require_payload(data)

    name = field(data, 'name')
    if name is MISSING or name is None or name == '':
        raise ValidationError(MSG_NAME_REQUIRED)

    return {
        'name': validate_string(
            name,
            empty_message=MSG_NAME_REQUIRED,
            type_message=MSG_NAME_TYPE,
            max_length=MAX_CATEGORY_NAME_LENGTH,
            long_message=MSG_NAME_TYPE,
        ),
        'description': validate_optional_text(
            data.get('description', ''),
            MSG_DESCRIPTION_INVALID,
            max_length=MAX_CATEGORY_DESCRIPTION_LENGTH,
        ),
        'color': _validate_color(data.get('color', DEFAULT_COLOR)),
    }


def load_update(data):
    """Valida o payload de `PUT /categories/<id>` — só os campos presentes."""
    require_payload(data)
    result = {}

    if 'name' in data:
        result['name'] = validate_string(
            data['name'],
            empty_message=MSG_NAME_REQUIRED,
            type_message=MSG_NAME_TYPE,
            max_length=MAX_CATEGORY_NAME_LENGTH,
            long_message=MSG_NAME_TYPE,
        )

    if 'description' in data:
        result['description'] = validate_optional_text(
            data['description'],
            MSG_DESCRIPTION_INVALID,
            max_length=MAX_CATEGORY_DESCRIPTION_LENGTH,
        )

    if 'color' in data:
        result['color'] = _validate_color(data['color'])

    return result
