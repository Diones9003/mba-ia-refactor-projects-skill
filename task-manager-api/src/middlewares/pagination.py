"""Paginação opcional das coleções.

As coleções originais faziam `.all()` sem limite. A paginação é **opt-in**: só entra
em ação quando a request traz `page` ou `per_page`, de modo que clientes existentes
continuam recebendo a coleção completa.
"""
from flask import current_app, request

from src.exceptions import ValidationError
from src.models.schemas.base import parse_int_param


def pagination_params():
    """Devolve `(limit, offset)` — `(None, None)` quando o cliente não pediu paginação."""
    if 'page' not in request.args and 'per_page' not in request.args:
        return None, None

    page = parse_int_param(request.args.get('page'), 'Parâmetro page inválido') or 1
    per_page = parse_int_param(
        request.args.get('per_page'), 'Parâmetro per_page inválido'
    ) or current_app.config['DEFAULT_PAGE_SIZE']

    if page < 1:
        raise ValidationError('Parâmetro page deve ser maior ou igual a 1')
    if per_page < 1:
        raise ValidationError('Parâmetro per_page deve ser maior ou igual a 1')

    max_page_size = current_app.config['MAX_PAGE_SIZE']
    if per_page > max_page_size:
        raise ValidationError(
            f'Parâmetro per_page excede o máximo de {max_page_size}'
        )

    return per_page, (page - 1) * per_page
