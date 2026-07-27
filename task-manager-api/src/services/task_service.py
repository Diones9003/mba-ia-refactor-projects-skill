"""Regras de negócio de task.

Recebe as dependências por construtor (models e o session do banco), sem tocar em
`request`/`response` — o que torna cada regra testável sem subir HTTP.
"""
from src.config.constants import (
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from src.exceptions import NotFoundError

MSG_TASK_NOT_FOUND = 'Task não encontrada'
MSG_USER_NOT_FOUND = 'Usuário não encontrado'
MSG_CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class TaskService:
    def __init__(self, session, task_model, user_model, category_model, notifier=None):
        self.session = session
        self.task_model = task_model
        self.user_model = user_model
        self.category_model = category_model
        self.notifier = notifier

    # --- Leitura ---

    def list_tasks(self, limit=None, offset=None):
        """Lista tasks com usuário e categoria já carregados (sem N+1)."""
        return self.task_model.list_all(
            limit=limit, offset=offset, with_relations=True
        )

    def get_task(self, task_id):
        task = self.task_model.get_by_id(task_id)
        if task is None:
            raise NotFoundError(MSG_TASK_NOT_FOUND)
        return task

    def list_by_user(self, user_id, limit=None, offset=None):
        self._require_user(user_id)
        return self.task_model.list_by_user(user_id, limit=limit, offset=offset)

    def search(self, term=None, status=None, priority=None, user_id=None,
               limit=None, offset=None):
        return self.task_model.search(
            term=term,
            status=status,
            priority=priority,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def build_stats(self):
        """Estatísticas de task — antes duplicadas em três endpoints."""
        by_status = self.task_model.count_by_status()
        total = sum(by_status.values())
        done = by_status[STATUS_DONE]
        return {
            'total': total,
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'done': done,
            'cancelled': by_status[STATUS_CANCELLED],
            'overdue': len(self.task_model.list_overdue()),
            'completion_rate': completion_rate(done, total),
        }

    # --- Escrita ---

    def create_task(self, payload):
        """Cria a task a partir de um payload já validado pelo schema."""
        self._require_related(payload.get('user_id'), payload.get('category_id'))

        task = self.task_model()
        task.title = payload['title']
        task.description = payload.get('description', '')
        task.status = payload['status']
        task.priority = payload['priority']
        task.user_id = payload.get('user_id')
        task.category_id = payload.get('category_id')
        task.due_date = payload.get('due_date')
        task.tag_list = payload.get('tags')

        self.session.add(task)
        self.session.commit()
        self._notify_assignment(task)
        return task

    def update_task(self, task_id, payload):
        task = self.get_task(task_id)
        previous_user_id = task.user_id

        self._require_related(
            payload.get('user_id') if 'user_id' in payload else None,
            payload.get('category_id') if 'category_id' in payload else None,
        )

        for attribute in ('title', 'description', 'status', 'priority',
                          'user_id', 'category_id', 'due_date'):
            if attribute in payload:
                setattr(task, attribute, payload[attribute])

        if 'tags' in payload:
            task.tag_list = payload['tags']

        task.touch()
        self.session.commit()

        if task.user_id and task.user_id != previous_user_id:
            self._notify_assignment(task)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        self.session.delete(task)
        self.session.commit()

    # --- Auxiliares ---

    def _require_user(self, user_id):
        if self.user_model.get_by_id(user_id) is None:
            raise NotFoundError(MSG_USER_NOT_FOUND)

    def _require_related(self, user_id, category_id):
        """Confere as FKs na mesma ordem do contrato original (usuário e depois categoria)."""
        if user_id:
            self._require_user(user_id)
        if category_id and self.category_model.get_by_id(category_id) is None:
            raise NotFoundError(MSG_CATEGORY_NOT_FOUND)

    def _notify_assignment(self, task):
        """Dispara a notificação de atribuição, se houver notificador configurado.

        O `NotificationService` original nunca era instanciado; agora ele é
        injetado e o efeito colateral vive no service, não no handler HTTP.
        """
        if self.notifier is None or not task.user_id:
            return
        user = self.user_model.get_by_id(task.user_id)
        if user is not None:
            self.notifier.notify_task_assigned(user, task)


def completion_rate(completed, total):
    """Percentual de conclusão — cálculo único, antes repetido em três lugares."""
    if not total:
        return 0
    return round((completed / total) * 100, 2)
