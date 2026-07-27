"""Serialização de categoria."""
from src.utils.datetime_utils import to_iso


def to_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': to_iso(category.created_at),
    }


def to_list_item(category, task_count):
    """Formato de `GET /categories`: base + total de tasks da categoria."""
    data = to_dict(category)
    data['task_count'] = task_count
    return data
