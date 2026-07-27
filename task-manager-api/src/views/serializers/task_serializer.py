"""Serialização de task — fonte única dos formatos de resposta.

O código original montava o dicionário da task campo a campo em três lugares
diferentes, com três subconjuntos de campos. Aqui cada formato é uma função
nomeada, e os três são derivados de `to_dict`.
"""
from src.utils.datetime_utils import to_iso


def to_dict(task):
    """Formato base — o mesmo que o `Task.to_dict()` original produzia."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': to_iso(task.created_at),
        'updated_at': to_iso(task.updated_at),
        'due_date': to_iso(task.due_date),
        'tags': task.tag_list,
    }


def to_detail(task):
    """Formato base + `overdue` — usado em `GET /tasks/<id>`."""
    data = to_dict(task)
    data['overdue'] = task.is_overdue()
    return data


def to_list_item(task):
    """Formato de `GET /tasks`: detalhe + nomes do usuário e da categoria.

    Usa os relacionamentos já carregados por eager loading, sem query extra.
    """
    data = to_detail(task)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def to_user_task_item(task):
    """Formato reduzido de `GET /users/<id>/tasks`."""
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': to_iso(task.created_at),
        'due_date': to_iso(task.due_date),
        'overdue': task.is_overdue(),
    }


def to_overdue_item(task, reference_moment):
    """Formato do item de atraso no relatório de resumo."""
    return {
        'id': task.id,
        'title': task.title,
        'due_date': to_iso(task.due_date),
        'days_overdue': (reference_moment - task.due_date).days,
    }
