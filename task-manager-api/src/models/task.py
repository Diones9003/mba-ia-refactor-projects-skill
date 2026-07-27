"""Model de task — acesso a dados e invariantes de domínio."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from src.config.constants import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    MAX_PRIORITY,
    MAX_TAGS_LENGTH,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    TAG_SEPARATOR,
    TERMINAL_STATUSES,
    VALID_STATUSES,
)
from src.extensions import db
from src.utils.datetime_utils import utcnow


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(MAX_TAGS_LENGTH), nullable=True)

    user = db.relationship('User', back_populates='tasks')
    category = db.relationship('Category', back_populates='tasks')

    # --- Regras de domínio ---

    def is_overdue(self):
        """Task vencida que ainda não chegou a um status terminal.

        Fonte **única** da regra: antes ela estava reimplementada em quatro
        handlers HTTP diferentes.
        """
        if self.due_date is None:
            return False
        return self.due_date < utcnow() and self.status not in TERMINAL_STATUSES

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [tag for tag in self.tags.split(TAG_SEPARATOR) if tag]

    @tag_list.setter
    def tag_list(self, value):
        if value is None:
            self.tags = None
        elif isinstance(value, (list, tuple)):
            self.tags = TAG_SEPARATOR.join(str(tag) for tag in value)
        else:
            self.tags = str(value)

    @staticmethod
    def is_valid_status(status):
        return status in VALID_STATUSES

    @staticmethod
    def is_valid_priority(priority):
        return isinstance(priority, int) and MIN_PRIORITY <= priority <= MAX_PRIORITY

    def touch(self):
        self.updated_at = utcnow()

    # --- Acesso a dados ---

    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_all(cls, limit=None, offset=None, with_relations=False):
        stmt = select(cls).order_by(cls.id)
        if with_relations:
            # Eager loading: elimina os 2N `query.get` que rodavam dentro do laço
            # de serialização em GET /tasks.
            stmt = stmt.options(selectinload(cls.user), selectinload(cls.category))
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset or 0)
        return list(db.session.scalars(stmt))

    @classmethod
    def list_by_user(cls, user_id, limit=None, offset=None):
        stmt = select(cls).filter_by(user_id=user_id).order_by(cls.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset or 0)
        return list(db.session.scalars(stmt))

    @classmethod
    def search(cls, term=None, status=None, priority=None, user_id=None,
               limit=None, offset=None):
        stmt = select(cls)
        if term:
            pattern = f'%{cls.escape_like(term)}%'
            stmt = stmt.filter(
                or_(
                    cls.title.like(pattern, escape='\\'),
                    cls.description.like(pattern, escape='\\'),
                )
            )
        if status:
            stmt = stmt.filter(cls.status == status)
        if priority is not None:
            stmt = stmt.filter(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.filter(cls.user_id == user_id)
        stmt = stmt.order_by(cls.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset or 0)
        return list(db.session.scalars(stmt))

    @staticmethod
    def escape_like(term):
        """Neutraliza os wildcards do LIKE vindos do usuário (`%`, `_`, `\\`)."""
        return (
            term.replace('\\', '\\\\')
            .replace('%', '\\%')
            .replace('_', '\\_')
        )

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count(cls.id))) or 0

    @classmethod
    def count_by_status(cls):
        """Contagem por status em **uma** query — antes eram 4 `COUNT` separados."""
        rows = db.session.execute(
            select(cls.status, func.count(cls.id)).group_by(cls.status)
        )
        counts = {status: 0 for status in VALID_STATUSES}
        for status, total in rows:
            counts[status] = total
        return counts

    @classmethod
    def count_by_priority(cls):
        """Contagem por prioridade em **uma** query — antes eram 5 `COUNT` separados."""
        rows = db.session.execute(
            select(cls.priority, func.count(cls.id)).group_by(cls.priority)
        )
        counts = {priority: 0 for priority in range(MIN_PRIORITY, MAX_PRIORITY + 1)}
        for priority, total in rows:
            if priority in counts:
                counts[priority] = total
        return counts

    @classmethod
    def count_by_category(cls):
        """Mapa `category_id -> total` em uma query (elimina o N+1 de GET /categories)."""
        rows = db.session.execute(
            select(cls.category_id, func.count(cls.id)).group_by(cls.category_id)
        )
        return {category_id: total for category_id, total in rows}

    @classmethod
    def list_overdue(cls):
        """Tasks vencidas e não terminais, resolvidas no banco (sem varrer tudo)."""
        stmt = (
            select(cls)
            .filter(cls.due_date.isnot(None))
            .filter(cls.due_date < utcnow())
            .filter(cls.status.notin_(TERMINAL_STATUSES))
            .order_by(cls.due_date)
        )
        return list(db.session.scalars(stmt))

    @classmethod
    def count_created_since(cls, moment):
        return db.session.scalar(
            select(func.count(cls.id)).filter(cls.created_at >= moment)
        ) or 0

    @classmethod
    def count_completed_since(cls, moment, done_status):
        return db.session.scalar(
            select(func.count(cls.id))
            .filter(cls.status == done_status)
            .filter(cls.updated_at >= moment)
        ) or 0

    @classmethod
    def aggregate_by_user(cls):
        """Total e concluídas por usuário em uma query (elimina o N+1 do relatório)."""
        from src.config.constants import STATUS_DONE

        rows = db.session.execute(
            select(
                cls.user_id,
                func.count(cls.id),
                func.sum(db.case((cls.status == STATUS_DONE, 1), else_=0)),
            ).group_by(cls.user_id)
        )
        return {
            user_id: {'total': total, 'completed': completed or 0}
            for user_id, total, completed in rows
        }

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
