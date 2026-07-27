"""Regras de negócio de categoria.

No código original este CRUD morava dentro de `routes/report_routes.py` — domínio
errado, o que deixava `GET /categories` registrado no blueprint de relatórios.
"""
from src.config.constants import DEFAULT_COLOR
from src.exceptions import NotFoundError

MSG_CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class CategoryService:
    def __init__(self, session, category_model, task_model):
        self.session = session
        self.category_model = category_model
        self.task_model = task_model

    def list_with_task_counts(self, limit=None, offset=None):
        """Categorias + total de tasks em duas queries fixas (antes era um N+1)."""
        categories = self.category_model.list_all(limit=limit, offset=offset)
        counts = self.task_model.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in categories]

    def get_category(self, category_id):
        category = self.category_model.get_by_id(category_id)
        if category is None:
            raise NotFoundError(MSG_CATEGORY_NOT_FOUND)
        return category

    def create_category(self, payload):
        category = self.category_model()
        category.name = payload['name']
        category.description = payload.get('description', '')
        category.color = payload.get('color', DEFAULT_COLOR)
        self.session.add(category)
        self.session.commit()
        return category

    def update_category(self, category_id, payload):
        category = self.get_category(category_id)
        for attribute in ('name', 'description', 'color'):
            if attribute in payload:
                setattr(category, attribute, payload[attribute])
        self.session.commit()
        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        self.session.delete(category)
        self.session.commit()
