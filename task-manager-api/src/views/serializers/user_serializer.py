"""Serialização de usuário.

Whitelist explícita de campos: o hash da senha **nunca** sai daqui. O
`User.to_dict()` original incluía `'password': self.password` e era devolvido
por `GET /users/<id>`, `POST /users` e `POST /login`.
"""
from src.utils.datetime_utils import to_iso
from src.views.serializers.task_serializer import to_dict as _task_to_dict


def to_public_dict(user):
    """Representação pública do usuário — sem credenciais."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': to_iso(user.created_at),
    }


def to_list_item(user, task_count):
    """Formato de `GET /users`: público + total de tasks."""
    data = to_public_dict(user)
    data['task_count'] = task_count
    return data


def to_detail(user, tasks):
    """Formato de `GET /users/<id>`: público + tasks do usuário."""
    data = to_public_dict(user)
    data['tasks'] = [_task_to_dict(task) for task in tasks]
    return data


def to_report_identity(user):
    """Identificação enxuta usada no relatório por usuário."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
    }
