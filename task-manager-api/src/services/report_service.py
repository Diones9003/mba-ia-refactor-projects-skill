"""Relatórios de produtividade.

Substitui o God Method `summary_report` (90 linhas, ~15 queries com dois N+1) por
um service que agrega no banco. As contagens por status, por prioridade e por
usuário passaram de 4+5+N queries para 3 agregações com `GROUP BY`.
"""
from datetime import timedelta

from src.config.constants import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    TERMINAL_STATUSES,
)
from src.services.task_service import completion_rate
from src.utils.datetime_utils import to_iso, utcnow
from src.views.serializers import task_serializer, user_serializer


class ReportService:
    def __init__(self, session, task_model, user_model, category_model):
        self.session = session
        self.task_model = task_model
        self.user_model = user_model
        self.category_model = category_model

    def build_summary(self):
        """Relatório geral — mesma estrutura de resposta do endpoint original."""
        now = utcnow()
        by_status = self.task_model.count_by_status()
        by_priority = self.task_model.count_by_priority()
        overdue_tasks = self.task_model.list_overdue()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        return {
            'generated_at': to_iso(now),
            'overview': {
                'total_tasks': self.task_model.count(),
                'total_users': self.user_model.count(),
                'total_categories': self.category_model.count(),
            },
            'tasks_by_status': {
                'pending': by_status[STATUS_PENDING],
                'in_progress': by_status[STATUS_IN_PROGRESS],
                'done': by_status[STATUS_DONE],
                'cancelled': by_status[STATUS_CANCELLED],
            },
            'tasks_by_priority': {
                label: by_priority.get(priority, 0)
                for priority, label in sorted(PRIORITY_LABELS.items())
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [
                    task_serializer.to_overdue_item(task, now)
                    for task in overdue_tasks
                ],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self.task_model.count_created_since(since),
                'tasks_completed_last_7_days': self.task_model.count_completed_since(
                    since, STATUS_DONE
                ),
            },
            'user_productivity': self._build_user_productivity(),
        }

    def _build_user_productivity(self):
        """Produtividade por usuário sem query dentro de laço."""
        aggregates = self.task_model.aggregate_by_user()
        rows = []
        for user in self.user_model.list_all():
            stats = aggregates.get(user.id, {'total': 0, 'completed': 0})
            total = stats['total']
            completed = stats['completed']
            rows.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': completion_rate(completed, total),
            })
        return rows

    def build_user_report(self, user):
        """Relatório individual — uma passada sobre as tasks do usuário."""
        tasks = self.task_model.list_by_user(user.id)
        counters = {
            STATUS_DONE: 0,
            STATUS_PENDING: 0,
            STATUS_IN_PROGRESS: 0,
            STATUS_CANCELLED: 0,
        }
        overdue = 0
        high_priority = 0
        now = utcnow()

        for task in tasks:
            if task.status in counters:
                counters[task.status] += 1
            if task.priority is not None and task.priority <= HIGH_PRIORITY_THRESHOLD:
                high_priority += 1
            if (
                task.due_date is not None
                and task.due_date < now
                and task.status not in TERMINAL_STATUSES
            ):
                overdue += 1

        total = len(tasks)
        return {
            'user': user_serializer.to_report_identity(user),
            'statistics': {
                'total_tasks': total,
                'done': counters[STATUS_DONE],
                'pending': counters[STATUS_PENDING],
                'in_progress': counters[STATUS_IN_PROGRESS],
                'cancelled': counters[STATUS_CANCELLED],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': completion_rate(counters[STATUS_DONE], total),
            },
        }
