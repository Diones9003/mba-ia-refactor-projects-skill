"""Model de usuário — acesso a dados e invariantes de domínio."""
import hashlib

from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import (
    DEFAULT_ROLE,
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    ROLE_ADMIN,
    VALID_ROLES,
)
from src.extensions import db
from src.utils.datetime_utils import utcnow

#: Tamanho de um hash MD5 hexadecimal — usado para reconhecer credenciais legadas.
_LEGACY_MD5_LENGTH = 32


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_EMAIL_LENGTH), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship(
        'Task',
        back_populates='user',
        # O cascade é responsabilidade do model, não da rota: antes o
        # user_routes.py apagava as tasks manualmente em um laço.
        cascade='all, delete-orphan',
        passive_deletes=False,
    )

    # --- Regras de domínio ---

    def set_password(self, raw_password):
        """Grava a senha usando hash com salt e fator de custo (scrypt)."""
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Confere a senha, aceitando credenciais MD5 legadas uma última vez.

        Bancos criados antes da refatoração guardam MD5 sem salt. Para não
        invalidar esses logins, o hash legado é aceito e imediatamente
        substituído por um hash forte (o chamador precisa fazer commit).
        """
        if self._is_legacy_hash():
            if hashlib.md5(raw_password.encode()).hexdigest() != self.password:
                return False
            self.set_password(raw_password)
            return True
        return check_password_hash(self.password, raw_password)

    def _is_legacy_hash(self):
        return (
            len(self.password or '') == _LEGACY_MD5_LENGTH
            and '$' not in self.password
        )

    def is_admin(self):
        return self.role == ROLE_ADMIN

    @staticmethod
    def is_valid_role(role):
        return role in VALID_ROLES

    # --- Acesso a dados ---

    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        return db.session.scalars(select(cls).filter_by(email=email)).first()

    @classmethod
    def email_taken_by_other(cls, email, user_id):
        """Diz se o e-mail já pertence a *outro* usuário."""
        existing = cls.get_by_email(email)
        return existing is not None and existing.id != user_id

    @classmethod
    def list_all(cls, limit=None, offset=None):
        stmt = select(cls).order_by(cls.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset or 0)
        return list(db.session.scalars(stmt))

    @classmethod
    def list_with_task_counts(cls, limit=None, offset=None):
        """Usuários + total de tasks em **uma** query (elimina o N+1 de `len(u.tasks)`)."""
        from src.models.task import Task

        stmt = (
            select(cls, func.count(Task.id))
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset or 0)
        return [(user, count) for user, count in db.session.execute(stmt)]

    @classmethod
    def count(cls):
        return db.session.scalar(select(func.count(cls.id))) or 0

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
