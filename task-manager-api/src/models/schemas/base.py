"""Blocos reutilizáveis de validação de entrada.

Substitui as validações inline duplicadas entre `create` e `update` de cada recurso.
As mensagens e a **ordem** das checagens reproduzem o contrato original; a diferença
é que agora o tipo é verificado antes da comparação, o que troca os antigos
`TypeError`/`ValueError` (que viravam 500 ou traceback) por um 400 descritivo.
"""
from src.exceptions import ValidationError

#: Sentinela para distinguir "campo ausente" de "campo enviado como null".
MISSING = object()


def require_payload(data):
    """Garante que o corpo é um objeto JSON não vazio."""
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def field(data, name):
    """Devolve o valor do campo ou `MISSING` se ele não veio no payload."""
    return data.get(name, MISSING) if isinstance(data, dict) else MISSING


def validate_string(value, *, empty_message, type_message,
                    min_length=None, short_message=None,
                    max_length=None, long_message=None):
    """Valida uma string obrigatória com limites de tamanho.

    Cada mensagem é injetada por quem chama, porque o contrato original usa textos
    diferentes para o mesmo campo em `create` e em `update`.
    """
    if value is None or value == '':
        raise ValidationError(empty_message)
    if not isinstance(value, str):
        raise ValidationError(type_message)
    text = value.strip()
    if not text:
        raise ValidationError(empty_message)
    if min_length is not None and len(text) < min_length:
        raise ValidationError(short_message)
    if max_length is not None and len(text) > max_length:
        raise ValidationError(long_message)
    return text


def validate_choice(value, choices, message):
    if value not in choices:
        raise ValidationError(message)
    return value


def validate_int_range(value, minimum, maximum, message):
    """Valida um inteiro dentro de um intervalo fechado.

    Booleanos são rejeitados de propósito: em Python `True` é `int`, mas
    `priority: true` não é uma prioridade válida.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(message)
    if value < minimum or value > maximum:
        raise ValidationError(message)
    return value


def validate_optional_text(value, message, max_length=None):
    """Texto opcional: aceita `None` ou string; rejeita outros tipos."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(message)
    if max_length is not None and len(value) > max_length:
        raise ValidationError(message)
    return value


def validate_bool(value, message):
    if not isinstance(value, bool):
        raise ValidationError(message)
    return value


def parse_int_param(raw, message):
    """Converte um parâmetro de query string em inteiro.

    Antes, `int(request.args.get(...))` sem tratamento estourava `ValueError`
    (500) para qualquer texto não numérico.
    """
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError(message) from None
