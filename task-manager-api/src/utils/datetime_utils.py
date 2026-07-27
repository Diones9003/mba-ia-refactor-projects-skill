"""Utilitários de data/hora.

Substitui as 18 chamadas a `datetime.utcnow()` (depreciado no Python 3.12) por um
ponto único baseado em `datetime.now(timezone.utc)`.

As colunas do banco guardam datetimes *naive* em UTC (comportamento herdado do
schema original), então `utcnow()` devolve naive para manter a compatibilidade
com os dados já gravados — mas o valor agora é derivado de um relógio ciente de
fuso, sem o warning de depreciação.
"""
from datetime import datetime, timezone

from src.config.constants import DATE_INPUT_FORMATS


def utcnow():
    """Agora, em UTC, como datetime *naive* (compatível com as colunas existentes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_naive_utc(value):
    """Normaliza um datetime para naive-UTC; devolve `None` para entrada vazia."""
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def parse_date(value, formats=DATE_INPUT_FORMATS):
    """Interpreta uma string de data nos formatos aceitos.

    Devolve `None` quando o valor não casa com nenhum formato — quem chama decide
    se isso é erro de validação.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return as_naive_utc(value)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def to_iso(value):
    """Serializa um datetime no mesmo formato textual usado pela API original."""
    return str(value) if value is not None else None
