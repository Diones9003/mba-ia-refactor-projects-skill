"""Model de categoria — acesso a dados e invariantes de domínio."""
import re

from sqlalchemy import func, select

from src.config.constants import (
    COLOR_PATTERN,
    DEFAULT_COLOR,
    MAX_CATEGORY_DESCRIPTION_LENGTH,
    MAX_CATEGORY_NAME_LENGTH,
)
from src.extensions import db
from src.utils.datetime_utils import utcnow

_COLOR_RE = re.compile(COLOR_PATTERN)


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(MAX_CATEGORY_NAME_LENGTH), nullable=False)
    description = db.Column(db.String(MAX_CATEGORY_DESCRIPTION_LENGTH), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    tasks = db.relationship('Task', back_populates='category')

    # --- Regras de domínio ---

    @staticmethod
    def is_valid_color(color):
        return bool(color) and bool(_COLOR_RE.match(color))

    # --- Acesso a dados ---

    @classmethod
    def get_by_id(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def list_all(cls, limit=None, offset=None):
        stmt = select(cls).order_by(cls.id)
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset or 0)
        return list(db.session.scalars(stmt))

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
